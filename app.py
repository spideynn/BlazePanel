# -*- coding: utf-8 -*-
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, render_template, flash
import getpass
import base64
import easygui

app = Flask(__name__)
### CONFIGURATION SECTION ###
### EDIT BELOW HERE ###
SECRET_KEY='8v0w9e8RNWEVRW90e8rnvWER9837R' # Match this with the secret key below.
app.config.update(dict(
    DATABASE=os.path.join('data/', 'blazegoat.db'),
    DEBUG=True,
    SECRET_KEY='8v0w9e8RNWEVRW90e8rnvWER9837R'
))
### EDIT ABOVE HERE ###

### ENCRYPT PASSWORDS ###
def encrypt(key, msg):
    encryped = []
    for i, c in enumerate(msg):
        key_c = ord(key[i % len(key)])
        msg_c = ord(c)
        encryped.append(chr((msg_c + key_c) % 127))
    return ''.join(encryped)

def decrypt(key, encryped):
    msg = []
    for i, c in enumerate(encryped):
        key_c = ord(key[i % len(key)])
        enc_c = ord(c)
        msg.append(chr((enc_c - key_c) % 127))
    return ''.join(msg)
### END ENCRYPTED PASSWORDS ###

def connect_db(): # Connect to the database specified in the config array.
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db(): # Initialize database if it doesn't exist.
    if os.path.exists("data/blazegoat.db"):
        print("Database exists, assuming schema does too.") # Assume that the schema is valid, and continue.
        db = sqlite3.connect('data/blazegoat.db')
        db.close()
    else:
        print("Database does not exist, creating.")
        username = easygui.enterbox('Please enter the admin account username.')
        password = encrypt(SECRET_KEY, easygui.passwordbox('Please enter a password that is longer than eight characters. (hidden)'))
        while(len(password) < 8):
            password = encrypt(SECRET_KEY, easygui.passwordbox('Password is less than eight characters\nPlease enter a password that is longer than eight characters. (hidden)'))
        email = easygui.enterbox('Please enter your email address.')
        db = sqlite3.connect('data/blazegoat.db')
        
        cursor = db.cursor() # Create the users table.
        cursor.execute('PRAGMA secure_delete = "1"') # Undeletable users and server data, preventing stolen data.
        
        cursor.execute('''
        CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE,
        email TEXT UNIQUE, password TEXT, rank INT, tempPass INTEGER)
        ''') # Create the servers database.
        cursor.execute('''
        CREATE TABLE servers(id INTEGER PRIMARY KEY, sid INTEGER UNIQUE,
        owner TEXT, jar TEXT)
        ''')
        db.commit()
        cursor.execute('INSERT INTO users (username, email, password, rank, tempPass) VALUES (?, ?, ?, 4, 0)', (username, email, password))
        db.commit()
        db.close()
        print("Sucessfully created database.")

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
        try: # None means that the username doesn't exist. TODO: Fix this so that it doesn't require a try statement.
            if request.form['username'] != db.execute('SELECT username FROM users WHERE username=?', (request.form['username'],)).fetchone()['username']:
                error = 'Invalid username.'
            elif request.form['password'] != decrypt(SECRET_KEY, db.execute('SELECT password FROM users WHERE username=?', (request.form['username'],)).fetchone()['password']):
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
                db.cursor().execute('INSERT INTO users (username, email, password, rank) VALUES (?, ?, ?, 1, 0)', 
                           [request.form['username'], request.form['email'], encrypt(SECRET_KEY, request.form['password'])])
                db.commit()
            except sqlite3.IntegrityError: # Username or email exists.
                error = 'Username or email already taken.'
            flash('Registration successful! You have been logged in.')
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('register.html', error=error)
    
@app.route('/servers/<sid>', methods=['GET', 'POST'])
def servers():
    db = get_db()
    error = None
    return render_template('servers.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None) # Pop the session, logging out the user.
    flash('You were logged out')
    return redirect(url_for('index'))
    
if __name__ == "__main__":
    init_db()
    app.debug = True
    app.run()