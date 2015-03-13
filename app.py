# -*- coding: utf-8 -*-
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, render_template, flash

app = Flask(__name__)

### EDIT BELOW HERE ###
app.config.update(dict(
    DATABASE=os.path.join('data/', 'blazegoat.db'),
    DEBUG=True,
    SECRET_KEY='8v0w9e8RNWE*VRW90e8rnvWER&9837R'
))
### EDIT ABOVE HERE ###

def connect_db(): # Connect to the database specified in the config array.
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db(): # Initialize database if it doesn't exist.
    if os.path.exists("data/blazegoat.db"):
        print("Database exists, assuming schema does too.")
        db = sqlite3.connect('data/blazegoat.db')
        db.close()
    else:
        print("Database does not exist, creating.")
        db = sqlite3.connect('data/blazegoat.db')
        cursor = db.cursor() # Create the users table.
        cursor.execute('''
        CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE,
        email TEXT UNIQUE, password TEXT, rank INT)
        ''') # Create the servers database.
        cursor.execute('''
        CREATE TABLE servers(id INTEGER PRIMARY KEY, sid INTEGER UNIQUE,
        owner TEXT, jar TEXT)
        ''')
        db.commit()
        db.close() 

def get_db(): # Gets the database from the config array.
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error): # On application close, close the database normally, as to not break the db.
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db().cursor()
    error = None
    if request.method == 'POST':
        try: # TypeError means that the username doesn't exist. TODO: Fix this so that it doesn't require a try statement.
            if request.form['username'] != db.execute('SELECT username FROM users WHERE username=?', (request.form['username'],)).fetchone()['username']:
                error = 'Invalid username.'
            elif request.form['password'] != db.execute('SELECT password FROM users WHERE username=?', (request.form['username'],)).fetchone()['password']:
                error = 'Invalid password'
            else:
                session['logged_in'] = True # Set the logged in cookie.
                flash('You were logged in')
                return redirect(url_for('index'))
        except TypeError:
            error = 'Invalid username.'
    return render_template('login.html', error=error)
    
@app.route('/signup', methods=['GET', 'POST'])
def register():
    db = get_db()
    error = None
    if request.method == 'POST':
        if request.form['password'] != request.form['confirmpassword']: # Doesn't match
            error = 'Your passwords do not match.'
        elif len(request.form['password']) <  8: 
            error =  'Your password must be eight characters or longer.'
        else: # Attempt to insert the user
            try:
                db.cursor().execute('INSERT INTO users (username, email, password, rank) VALUES (?, ?, ?, 1)', 
                           [request.form['username'], request.form['email'], request.form['password']])
                db.commit()
            except sqlite3.IntegrityError: # Username or email exists.
                error = 'Username or email already taken.'
            flash('Registration successful! You have been logged in.')
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('register.html', error=error)
    
@app.route('/debug')
def debug():
    db = get_db().cursor()
    value = db.execute('SELECT username FROM users WHERE username=?',("spideynn",)).fetchone()
    return value[0]

@app.route('/logout')
def logout():
    session.pop('logged_in', None) # Pop the session, logging out the user.
    flash('You were logged out')
    return redirect(url_for('index'))
    
if __name__ == "__main__":
    init_db()
    app.debug = True
    app.run()