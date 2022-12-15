from flask import Flask, render_template,  request,  redirect, escape, session
from DBcm import UseDatabase, CredentialsError, ConnectionError, SQLError
from search4web import search4letters
from collections import Counter
import time
import os

app = Flask(__name__)
app.secret_key = 'hola'
app.id_user = 0

# Para las imagenes
IMG_FOLDER = os.path.join('static', 'img')
app.config['UPLOAD_FOLDER'] = IMG_FOLDER

app.id_user = 0

app.config['dbconfig'] = {
        'host': '127.0.0.1',
        'user': 'root',
        'password': 'SQL21',
        'database': 'search_log_webapp',
        'auth_plugin': 'mysql_native_password'
    }

@app.route('/')
@app.route('/index')
def index_page() -> 'html':
    Flask_Logo = os.path.join(app.config['UPLOAD_FOLDER'], 'icon.jpg')
    Flask_Logo2 = os.path.join(app.config['UPLOAD_FOLDER'], 'icon2.jpg')
    return render_template('index.html',user_image=Flask_Logo,user_image2=Flask_Logo2)


@app.route('/login')
def entry_page2() -> 'html':
    Flask_Logo = os.path.join(app.config['UPLOAD_FOLDER'], 'icon.jpg')
    Flask_Logo2 = os.path.join(app.config['UPLOAD_FOLDER'], 'icon2.jpg')
    return render_template('login.html', the_title='Welcome to search for letters on the web!', user_image=Flask_Logo,
                           user_image2=Flask_Logo2)

@app.route('/log', methods=['POST'])
def login() -> None:
    print("Entramos en el login")
    user = request.form['user_name']
    pswd = request.form['password']

    with UseDatabase(app.config['dbconfig']) as cursor:
        _SQL = """select id_user from users1 where user_name = %s and password = %s"""
        cursor.execute(_SQL, (user, pswd))
        contents = cursor.fetchall()


    if len(contents) == 1:
        app.id_user = contents[0][0]
        id_user = app.id_user
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """select count from dbvisits1 where id_user = %s"""
            cursor.execute(_SQL, (id_user,))
            contents = cursor.fetchall()

        count = contents[0][0]
        count = count + 1

        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """update dbvisits1 SET count = %s where id_user = %s"""
            cursor.execute(_SQL, (count, app.id_user))

        session['logged_in'] = True
        Flask_Logo = os.path.join(app.config['UPLOAD_FOLDER'], 'icon.jpg')
        Flask_Logo2 = os.path.join(app.config['UPLOAD_FOLDER'], 'icon2.jpg')
        return render_template('index.html', user_image=Flask_Logo, user_image2=Flask_Logo2)
    else:
        print("El usuario no es correcto")
        return "El usuario introducido es incorrecto o no existe"


@app.route('/newuser', methods=['POST'])
def createNewUser() -> None:
    user = request.form['new_user_name']
    pswd = request.form['new_password']

    with UseDatabase(app.config['dbconfig']) as cursor:
        _SQL = """select id_user from users1 where user_name = %s"""
        cursor.execute(_SQL, (user,))
        contents = cursor.fetchall()

    if len(contents) == 0:
        print("El usuario no existe, lo creamos")
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """insert into users1 (user_name, password) values (%s, %s)"""
            cursor.execute(_SQL, (user, pswd))

        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """select id_user from users1 where user_name = %s and password = %s"""
            cursor.execute(_SQL, (user, pswd))
            contents = cursor.fetchall()

        app.id_user = contents[0][0]

        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """insert into dbvisits1 (id_user, count) values (%s, %s)"""
            cursor.execute(_SQL, (app.id_user, 1))

        session['logged_in'] = True

        Flask_Logo = os.path.join(app.config['UPLOAD_FOLDER'], 'icon.jpg')
        Flask_Logo2 = os.path.join(app.config['UPLOAD_FOLDER'], 'icon2.jpg')
        return render_template('index.html', user_image=Flask_Logo, user_image2=Flask_Logo2)
    else:
        print("El usuario ya esta en la base de datos")
        return "Este usuario ya esta en uso, por favor introduce un nuevo nombre de usuario"


@app.route('/entry')
def entry_page() -> 'html':
    Flask_Logo = os.path.join(app.config['UPLOAD_FOLDER'], 'icon.jpg')
    Flask_Logo2 = os.path.join(app.config['UPLOAD_FOLDER'], 'icon2.jpg')
    return render_template('entry.html', the_title='Welcome to search for letters on the web!',user_image=Flask_Logo,user_image2=Flask_Logo2)

@app.route('/search', methods=['POST'])
def do_search() -> str:
    phrase = request.form['phrase']
    letters = request.form['letters']
    title = 'Here are your results: '
    results = str(search4letters(phrase, letters))
    id_user = app.id_user
    with UseDatabase(app.config['dbconfig']) as cursor:
         _SQL = """insert into log6 (phrase, letters, results, id_user) values (%s, %s, %s, %s)"""
         cursor.execute(_SQL, (request.form['phrase'], request.form['letters'], results, id_user))
    #log_request(request, results)
    return render_template('results.html', the_title = title, the_phrase = phrase, the_letters = letters, the_results = results)




@app.route('/viewlog')
def view_the_log() -> str:
    with open('search.log', 'r') as log:
        contents = log.read()
    return contents

def getTopUsers():
    with UseDatabase(app.config['dbconfig']) as cursor:
        _SQL = """select * from users1"""
        cursor.execute(_SQL)
        users = cursor.fetchall()

        _SQL = """select * from dbvisits1"""
        cursor.execute(_SQL)
        visits = cursor.fetchall()

    res = []
    for i in users:
        for j in visits:
            if i[0] == j[0]:
                res.append((i[1], j[1]))

    return(res)

def getTopWords():
    with UseDatabase(app.config['dbconfig']) as cursor:
        _SQL = """select phrase from log6"""
        cursor.execute(_SQL)
        phrases = cursor.fetchall()

    words = []
    for i in phrases:
        p = i[0].split()
        for j in p:
            words.append(j)

    c = Counter(words)
    w = c.items()
    w = list(w)
    return w

@app.route('/stats')
def view_stats() -> 'html':
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """select count(*) ip from log6"""
            cursor.execute(_SQL)
            n = cursor.fetchall()

            _SQL = """select letters from log6"""
            cursor.execute(_SQL)
            l = Counter(cursor.fetchall())
            letters = l.most_common()


            _SQL = """select ip from log6"""
            cursor.execute(_SQL)
            l = Counter(cursor.fetchall())
            ip = l.most_common()

            _SQL = """select browser_string from log6"""
            cursor.execute(_SQL)
            l = Counter(cursor.fetchall())
            browser = l.most_common()

            _SQL = """select count(*) ip from log6 where id_user = %s"""
            cursor.execute(_SQL, (app.id_user,))
            n1 = cursor.fetchall()

            _SQL = """select letters from log6 where id_user = %s"""
            cursor.execute(_SQL, (app.id_user,))
            l = Counter(cursor.fetchall())
            letters1 = l.most_common()

            _SQL = """select ip from log6 where id_user = %s"""
            cursor.execute(_SQL, (app.id_user,))
            l = Counter(cursor.fetchall())
            ip1 = l.most_common()

            _SQL = """select browser_string from log6 where id_user = %s"""
            cursor.execute(_SQL, (app.id_user,))
            l = Counter(cursor.fetchall())
            browser1 = l.most_common()

        top5Users = getTopUsers()
        n_anonimo = top5Users[0][1]
        top5Users.pop(0)
        top5Users.sort(key = lambda x: x[1], reverse = True)

        top5Words = getTopWords()
        return render_template('stats.html',
                                the_title = 'Stats',
                                n_request = n[0][0],
                                common_letters = letters[0][0][0],
                                ip_addr = ip[0][0][0],
                                browser = browser[0][0][0],
                                n_request1 = n1[0][0],
                                common_letters1 = letters1[0][0][0],
                                ip_addr1 = ip1[0][0][0],
                                browser1 = browser1[0][0][0],
                                n_anonimo = n_anonimo,
                                rows = top5Users,
                                words = top5Words
                               )

    except ConnectionError as err:
        print('Is your database switched on? Error: ', str(err))

    except CredentialsError as err:
        print('User-id/Password issues - ', str(err))

    except Exception as err:
        print("Something went wrong: ", str(err))

    return 'Error'

@app.route('/logged')
def do_login() -> str:
    session['logged_in'] = True
    return 'You are now logged in.'

@app.route('/logout')
def do_logout() -> str:
    session.pop('logged_in')
    return 'Bye. You are now logged out'

@app.route('/status')
def check_status() -> str:
    if 'logged_in' in session:
        return 'You are currently logged in.'
    return 'You are NOT logged in.'

if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(debug=True, port=5000)