# -*- coding: utf-8 -*-
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, render_template, flash

app = Flask(__name__)

app.config.update(dict(
    DATABASE=os.path.join('data/', 'blazegoat.db'),
    DEBUG=True,
    SECRET_KEY='8v0w9e8RNWE*VRW90e8rnvWER&9837R'
))


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    if os.path.exists("data/blazegoat.db"):
        print("Database exists, assuming schema does too.")
        db = sqlite3.connect('data/blazegoat.db')
        db.close()
    else:
        print("Database does not exist, creating.")
        db = sqlite3.connect('data/blazegoat.db')
        cursor = db.cursor()
        cursor.execute('''
        CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT unique,
        email TEXT unique, password TEXT, rank INT)
        ''')
        cursor.execute('''
        CREATE TABLE servers(id INTEGER PRIMARY KEY, sid INTEGER unique,
        owner TEXT, jar TEXT)
        ''')
        db.commit()
        db.close() 

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
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
        if request.form['username'] != db.execute('SELECT username FROM users WHERE username=?', (request.form['username'],)).fetchone()['username']:
            error = 'Invalid username.'
        elif request.form['password'] != db.execute('SELECT password FROM users WHERE username=? AND password=?', (request.form['username'], request.form['password'],)).fetchone()['password']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('index'))
    return render_template('login.html', error=error)
    
@app.route('/debug')
def debug():
    db = get_db().cursor()
    value = db.execute('SELECT username FROM users WHERE username=?',("spideynn",)).fetchone()
    return value[0]

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))
    
if __name__ == "__main__":
    init_db()
    app.debug = True
    app.run()