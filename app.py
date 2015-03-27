# -*- coding: utf-8 -*-
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, render_template, flash
import easygui

app = Flask(__name__)
### CONFIGURATION SECTION ###
### EDIT BELOW HERE ###
SECRET_KEY='8v0w9e8RNWEVRW90e8rnvWER9837R' # Match this with the secret key below.
app.config.update(dict(
    DATABASE=os.path.join('data/', 'blazegoat.db'),
    STATIC_FOLDER='static/',
    DEBUG=True,
    SECRET_KEY='8v0w9e8RNWEVRW90e8rnvWER9837R'
))
### EDIT ABOVE HERE ###

### ENCRYPTED PASSWORDS [using bcrypt-utils]###
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

### START DATABASE SETUP AND DETECTION ###
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
        cursor.execute('PRAGMA secure_delete = "1"') # Undeletable users and server data, preventing stolen data like usernames and passwords.
        
        cursor.execute('''
        CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE,
        email TEXT UNIQUE, password TEXT, rank INT, tempPass INTEGER)
        ''') # Create the servers database.
        cursor.execute('''
        CREATE TABLE servers(sid INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, name TEXT,
        owner TEXT, jartype TEXT, memory INT, customJartypePath STRING, worldName STRING)
        ''')
        db.commit()
        cursor.execute('INSERT INTO users (username, email, password, rank, tempPass) VALUES (?, ?, ?, 4, 0)', (username, email, password))
        db.commit()
        db.close()
        print("Sucessfully created database.")
### END DATABASE SETUP AND DETECTION ###

def get_db(): # Gets the database from the config array, connects, and returns the connection item.
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

### ERROR HANDLERS ###
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(410)
def page_gone(e):
    return render_template('errors/410.html'), 410

@app.errorhandler(403)
def page_no_access(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def page_error(e):
    return render_template('errors/500.html'), 500
    
@app.errorhandler(400)
def page_bad_request(e):
    return render_template('errors/400.html'), 400
### END ERROR HANDLERS ###
    
@app.teardown_appcontext
def close_db(error): # On application close, close the database normally, as to not break the db.
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    cur = g.db.execute('select title, text from entries order by id desc')
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    return render_template('index.html', entries=entries)

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
                session['username'] = request.form['username'] # Store the username as a session cookie
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
        if request.form['username'] == 'admin' or 'administrator':
            error = 'That username is reserved.'
        elif len(request.form['password']) <  8: 
            error =  'Your password must be eight characters or longer.'
        else: # Attempt to insert the user
            try:
                db.cursor().execute('INSERT INTO users (username, email, password, rank, tempPass) VALUES (?, ?, ?, 1, 0)', 
                           [request.form['username'], request.form['email'], encrypt(SECRET_KEY, request.form['password'])])
                db.commit()
            except sqlite3.IntegrityError: # Username or email exists.
                error = 'Username or email already taken.'
            flash('Registration successful! You have been logged in.')
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('register.html', error=error)
    
@app.route('/users/changepass', methods=['GET','POST'])
def changepass():
    db = get_db()
    error = None
    if request.method == 'POST':
        if request.form['oldpassword'] != decrypt(SECRET_KEY, db.execute('SELECT password FROM users WHERE username=?', (session['username'],)).fetchone()['password']):
            error = 'Your old password is incorrect.'
        if request.form['newpassword'] != request.form['confirmpassword']:
            error = 'Your new passwords do not match.'
        if request.form['oldpassword'] == request.form['newpassword']:
            error = 'Your new password cannot match your old password.'
        if request.form['newpassword'] == request.form['confirmpassword']:
            username = session['username'] # Temp fix: Prevents a statement error from occuring.
            password = encrypt(SECRET_KEY, request.form['newpassword']) # Temp fix: Prevents a statement error from occuring.
            cursor = db.cursor()
            cursor.execute('UPDATE users SET password=? WHERE username=?', [password, username,])
            db.commit()
            session.pop('logged_in', None) # Pop the session, logging out the user.
            session.pop('username', None) # Pop the username session cookie                
            flash('Your password has been updated. Please login again.')
            return redirect(url_for('index'))
    return render_template('usercp/changepass.html', error=error)
    
@app.route('/servers/create', methods=['GET', 'POST'])
def createServer():
    db = get_db()
    error = None
    if request.method == 'POST':
        db.cursor().execute('INSERT INTO servers (owner, jartype) VALUES (?,?)', [str(session['username']), str(request.form.getlist('jartype')), ])
        flash('Your server has been created with the following name: ' + request.form['servername'])
    return render_template('servercp/createserver.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None) # Pop the session, logging out the user.
    session.pop('username', None) # Pop the username session cookie
    flash('You were logged out.')
    return redirect(url_for('index'))
    
@app.route('/servers/id/<sid>/index', methods=['GET','POST'])
def serverIndex(sid):
    db = get_db()
    error = None
    if request.method == 'POST':
        if request.form['name'] == None:
            error = 'The server name cannot be empty.'
        db.cursor().execute('UPDATE servers SET jartype=?, name=? WHERE sid=?', [request.form['jartype'], request.form['name'], sid])
    return render_template('servercp/serverpanel.html', error=error)

if __name__ == "__main__":
    init_db()
    app.debug = True
    app.run(host='0.0.0.0')
