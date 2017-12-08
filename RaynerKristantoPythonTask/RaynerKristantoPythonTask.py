import os
import sqlite3
from .RaynerKristantoPythonTask import *
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'RaynerKristantoPythonTask.db'),
    SECRET_KEY='l#2l*82pc0z#slh9o^bso(^dqr&-3^btpb&!_--%+q04279^ka',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('RAYNERKRISTANTOPYTHONTASK_SETTINGS', silent=True)

# DB Functions
def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

# View functions
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/add', methods=['POST'])
def add_user():
    db = get_db()
    hashed_password = pbkdf2_sha256.encrypt(request.form['password'], rounds=100, salt_size=16)
    db.execute('insert into users (username, password) values (?, ?)',
                 [request.form['username'], hashed_password])
    db.commit()
    flash('Sucessfully signed up')
    return render_template('home.html', user=request.form['username'], password=request.form['password'], hashed=hashed_password)

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    db = get_db()

    if request.method == 'POST':
        string = "select * from users where username =='" + request.form['username'] + "'"
        matching_users = db.execute(string)
        for user in matching_users:
            if (pbkdf2_sha256.verify(request.form['password'], user['password'])):
                session['logged_in'] = True
                flash('You were logged in')
                return render_template('home.html', user=request.form['username'], password=request.form['password'], hashed=user['password'])

        # no matching users
        error = 'Invalid credentials'
    return render_template('login.html', error=error)

@app.route('/create_account')
def create_account():
    return render_template('create_account.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))
