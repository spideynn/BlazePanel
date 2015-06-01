# -*- coding: utf-8 -*-
import os
import sqlite3
import psutil
from flask import Flask, request, session, g, redirect, url_for, render_template, flash, jsonify, abort
import api.wrapper
from flask.ext.logging import Filter
import getpass
from pymlconf import ConfigManager

app = Flask(__name__)

logFilter = Filter('static', '_api') # Filter out requests to static and to _api to prevent AJAX spam.

### CONFIGURATION SECTION ###
initial_config = '''
port: 8080
debug: true
secret_key: enter_a_key_here
server_creation_locked: true
'''

cfg = ConfigManager()
cfg.load_files(["data/blazegoat_panel.conf"]) # Load the panel configuration.

app.config.update(dict(
    DATABASE=os.path.join('data/', 'blazegoat.db'),
    STATIC_FOLDER='static/',
    DEBUG=cfg.debug,
    SECRET_KEY=cfg.secret_key,
    server_creation_locked=cfg.server_creation_locked
))
### END CONFIGURATION SECTION ###

SECRET_KEY = app.config['SECRET_KEY'] # Clone the secret key for use in other methods easily

### ENCRYPTED PASSWORDS [using bcrypt-utils]###
def encrypt(key, msg):
    encryped = []
    for i, c in enumerate(msg): # Iterate (count through) items and characters
        key_c = ord(key[i % len(key)]) # Convert to ASCII with the given key and length of key.
        msg_c = ord(c) # Convert to ASCII with the given message and character.
        encryped.append(chr((msg_c + key_c) % 127)) # Append characters to the end of the encrypted array.
    return ''.join(encryped) # Join text array together in an empty string, and return it.

def decrypt(key, encryped):
    msg = []
    for i, c in enumerate(encryped): # Iterate (count through) items and characters
        key_c = ord(key[i % len(key)]) # Convert to ASCII with the given key and length of key.
        enc_c = ord(c) # Convert to ASCII with the given message and character.
        msg.append(chr((enc_c - key_c) % 127)) # Append characters to the end of the encrypted array.
    return ''.join(msg) # Join text array together in an empty string, and return it.
### END ENCRYPTED PASSWORDS ###

### START DATABASE SETUP AND DETECTION ###
def connect_db(): # Connect to the database specified in the config array.
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv # Returns connection item, removing the need to make multiple blocking connections.

def init_db(): # Initialize database if it doesn't exist.
    if os.path.exists("data/blazegoat.db"):
        print("Database exists, assuming schema does too.") # Assume that the schema is valid, and continue.
        db = sqlite3.connect('data/blazegoat.db')
        db.close()
    else:
        print("Database does not exist, creating.")
        username = input('Please enter the admin account username. ')
        password = encrypt(SECRET_KEY, getpass.getpass('Please enter a password that is longer than eight characters. (hidden)' ))
        while(len(password) < 8):
            password = encrypt(SECRET_KEY, getpass.getpass('Password is less than eight characters\nPlease enter a password that is longer than eight characters. (hidden) '))
        email = input('Please enter your email address. ')
        db = sqlite3.connect('data/blazegoat.db') # Connect to the database, creating it.

        cursor = db.cursor() # Create the users table.
        cursor.execute('PRAGMA secure_delete = "1"') # Undeletable users and server data, preventing stolen data like usernames and passwords.

        cursor.execute('''
        CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE,
        email TEXT UNIQUE, password TEXT, rank INT, tempPass INTEGER)
        ''') # Create the users database.
        cursor.execute('''
        CREATE TABLE servers(sid INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, name TEXT,
        owner TEXT, jartype TEXT, memory INT, customJartypePath STRING, worldName STRING)
        ''') # Create the servers database.
        db.commit()
        cursor.execute('INSERT INTO users (username, email, password, rank, tempPass) VALUES (?, ?, ?, 1, 0)', (username, email, password))
        db.commit() # Insert the user's info that was provided.
        db.close() # Close connection.
        print("Sucessfully created database.")
### END DATABASE SETUP AND DETECTION ###

# User Rank 1 - Administrator - Full access to everything
# User Rank 2 - Moderator - Access to other people's server(s)
# User Rank 3 - Trusted User - Change advanced settings with their server(s)
# User Rank 4 - Normal User - Normal access to their server(s)

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
    if hasattr(g, 'sqlite_db'): # Check global config for the sqlite attribute
        g.sqlite_db.close() # Close the database.

@app.route('/')
def index():
    db = get_db()
    if not session.get('logged_in'):
        session['username'] = None
    cur = db.execute('select name, owner, jartype, sid from servers order by sid desc')
    servers = [dict(name=row[0], owner=row[1], jartype=row[2], sid=row[3]) for row in cur.fetchall()] # Create a dictionary of servers w/ jartype and owner.
    return render_template('index.html', servers=servers)

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
        if request.form['username'].lower() == 'admin' or request.form['username'].lower() == 'administrator': # User tries to use a reserved username.
            error = 'That username is reserved.'
        elif len(request.form['password']) <  8:
            error =  'Your password must be eight characters or longer.'
        else: # Attempt to insert the user
            try:
                db.cursor().execute('INSERT INTO users (username, email, password, rank, tempPass) VALUES (?, ?, ?, 4, 0)',
                           [request.form['username'].lower(), request.form['email'].lower(), encrypt(SECRET_KEY, request.form['password'])])
                db.commit()
            except sqlite3.IntegrityError: # Username or email exists.
                error = 'Username or email already taken.'
            flash('Registration successful! You have been logged in.')
            session['username'] = request.form['username']
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('register.html', error=error)

@app.route('/users/changepass', methods=['GET','POST'])
def changepass():
    db = get_db()
    error = None
    if 'logged_in' in session != True and 'username' in session == None:
        abort(403)
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
            flash('Your password has been updated.')
            return redirect(url_for('index'))
    return render_template('usercp/changepass.html', error=error)

@app.route('/servers/create', methods=['GET', 'POST'])
def createServer():
    db = get_db()
    error = None
    if request.method == 'POST' and app.config['server_creation_locked'] == False:
        db.cursor().execute('INSERT INTO servers (owner, name, jartype) VALUES (?,?,?)', [str(session['username']), request.form['servername'], str(request.form.getlist('jartype')), ])
        db.commit()
        flash('Your server has been created with the following name: ' + request.form['servername'])
    else:
        error = "Server creation has been locked by the administrators."
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
    if request.method == 'GET':
        try:
            if db.execute('SELECT sid FROM servers WHERE sid=?', (sid,)).fetchone()['sid'] is None: # If server doesn't exist, throws TypeError (None)
                return render_template('errors/404.html')
            elif db.execute('SELECT rank FROM users WHERE username=?', (session["username"],)) == '1':
                return render_template('servercp/serverpanel.html', error=error, sid=sid)
            elif db.execute('SELECT owner FROM servers WHERE sid=?', (sid,)).fetchone()['owner'].lower() == session["username"].lower():
                return render_template('servercp/serverpanel.html', error=error, sid=sid)
            else:
                abort(403)
        except TypeError:
            return render_template('errors/404.html')
    return render_template('servercp/serverpanel.html', error=error, sid=sid)

    if request.method == 'POST':
        if request.form['name'] == None:
            error = 'The server name cannot be empty.'
        db.cursor().execute('UPDATE servers SET jartype=?, name=? WHERE sid=?', [request.form['jartype'], request.form['name'], sid])
        db.commit()
    return render_template('servercp/serverpanel.html', error=error, sid=sid)

@app.route('/servers/id/<sid>/_<option>', methods=["GET", "POST"])
def serverFunctions(sid, option):
    if request.method == 'GET':
        if option == 'api':
            cpu=psutil.cpu_percent() # Gets percentage of CPU Usage
            ram=psutil.virtual_memory() # Remeber, this is in bytes!
            pid="Server not online." # Process ID, not yet implemented.
            players='0' # Number of players
            playerlist=["No players are online"]
            return jsonify(cpu=cpu, ram=ram, pid=pid, players=players, playerList=playerlist) # Convert variables to JSON.

@app.route('/admin')
def adminPanel():
    if session.get('logged_in') == True:
        return render_template('admincp/adminindex.html')
    if session.get('logged_in') == False or None:
        abort(403)
    abort(403)

@app.route('/admin/settings/users')
def adminUsers():
    if session.get('logged_in') == True:
        db = get_db()
        cur = db.execute('select username, email, rank from users order by id desc')
        users = [dict(username=row[0], email=row[1], rank=row[2]) for row in cur.fetchall()]
        return render_template('admincp/adminusers.html', users=users)
    if session.get('logged_in') == False or None:
        abort(403)
    abort(403)

@app.route('/admin/settings/servers')
def adminServers():
    if session.get('logged_in') == True:
        return render_template('admincp/adminservers.html')
    if session.get('logged_in') == False or None:
        abort(403)
    abort(403)

@app.route('/admin/settings/panel')
def adminPanelSettings():
    if session.get('logged_in') == True:
        return render_template('admincp/adminsettings.html')
    if session.get('logged_in') == False or None:
        abort(403)
    abort(403)

if __name__ == "__main__":
    init_db()
    app.debug = cfg.debug
    app.run(host=str(os.getenv('IP', "0.0.0.0")), port=int(os.getenv('PORT', cfg.port)))
