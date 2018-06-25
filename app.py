from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug import secure_filename
from flask_cas import CAS

import os
import imghdr

app = Flask(__name__)
CAS(app)

import sys, random, dbconn2, datetime
import general as G
import treasurer as T
import sofc as S
import admin as A

app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +
                                          'abcdefghijklmnopqrstuvxyz' +
                                          '0123456789'))
                           for i in range(20) ])
app.config['TRAP_BAD_REQUEST_ERRORS'] = True
app.config['CAS_SERVER'] = 'https://login.wellesley.edu:443'
app.config['CAS_AFTER_LOGIN'] = 'home'
app.config['CAS_LOGIN_ROUTE'] = '/module.php/casserver/cas.php/login'
app.config['CAS_LOGOUT_ROUTE'] = '/module.php/casserver/cas.php/logout'
app.config['CAS_AFTER_LOGOUT'] = 'login'
app.config['CAS_VALIDATE_ROUTE'] = '/module.php/casserver/serviceValidate.php'

db = 'mshen4_db'

# ------------------------------------------------------------------------------
# ROUTES

@app.route('/', methods=['GET'])
def landing():
    # redirect to home if logged in already
    if 'CAS_ATTRIBUTES' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

# login
@app.route('/login/', methods=['GET', 'POST'])
def login():
    # go to home if already logged in
    if 'CAS_USERNAME' in session:
        return redirect(url_for('home'))
    # render empty login page
    if request.method == 'GET':
        return render_template('login.html')

# display home
@app.route('/home/')
def displayHome():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        G.addUser(conn, username)
        treasurer = T.isTreasurer(conn, username)
        sofc = S.isSOFC(conn, username)
        admin = A.isAdmin(conn, username)

        # redirect automatically to general if not treasurer, sofc, or admin
        if not (treasurer or sofc or admin):
            return redirect(url_for('general'))

        return render_template('home.html',
                               treasurer=treasurer,
                               sofc=sofc,
                               admin=admin)

    else:
        return redirect(url_for('login'))

# home routes
@app.route('/home/', methods=['POST'])
def home():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        treasurer = T.isTreasurer(conn, username)
        sofc = S.isSOFC(conn, username)
        admin = A.isAdmin(conn, username)
    else:
        return redirect(url_for('login'))

    # general member
    if request.form['submit'] == "GENERAL MEMBER":
        return redirect(url_for('general'))

    # treasurer
    if request.form['submit'] == "TREASURER":
        return redirect(url_for('treasurer'))

    # sofc member
    if request.form['submit'] == "SOFC MEMBER":
        return redirect(url_for('sofc'))

    # admin
    if request.form['submit'] == "ADMIN":
        return redirect(url_for('admin'))

# general route
@app.route('/general/', methods=['GET'])
def general():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        treasurer = T.isTreasurer(conn, username)
        sofc = S.isSOFC(conn, username)
        admin = A.isAdmin(conn, username)
        return render_template('general.html')
    else:
        return redirect(url_for('login'))

# display treaurer
@app.route('/treasurer/', methods=['GET', 'POST'])
def displayTreasurer():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        treasurer = T.isTreasurer(conn, username)
        if treasurer:
            return render_template('treasurer.html',
                                   username=username)
    else:
        return redirect(url_for('login'))

# treaurer routes
@app.route('/treasurer/', methods=['POST'])
def treasurer():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        treasurer = T.isTreasurer(conn, username)
        if treasurer:
            pass
    else:
        return redirect(url_for('login'))

# display sofc
@app.route('/sofc/')
def displaySOFC():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        sofc = S.isSOFC(conn, username)
        if sofc:
            return render_template('sofc.html',
                                   username=username)
    else:
        return redirect(url_for('login'))

# sofc route
@app.route('/sofc/', methods=['POST'])
def sofc():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        sofc = S.isSOFC(conn, username)
        if sofc:
            pass
    else:
        return redirect(url_for('login'))

# display admin
@app.route('/admin/')
def displayAdmin():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        if admin:
            return render_template('admin.html',
                                   username=username)
    else:
        return redirect(url_for('login'))

# admin route
@app.route('/admin/', methods=['POST'])
def admin():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        if admin:
            html = request.form['submit']
            if html == "USERS":
                return redirect(url_for('adminUsers'))
            if html == "ORGS":
                return redirect(url_for('adminOrgs'))
            if html == "FUNDING DEADLINES":
                return redirect(url_for('adminDeadlines'))
    else:
        return redirect(url_for('login'))

# admin users display
@app.route('/adminUsers/')
def displayAdminUser():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        if admin:
            return render_template('adminUsers.html',
                                   username=username)
    else:
        return redirect(url_for('login'))

# admin users route
@app.route('/adminUsers/', methods=['POST'])
def adminUser():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        if admin:
            act = request.form['submit']
            if act == "addTreasure":
                orgName = request.form['orgName']
                treasurer = request.form['username']
                A.addTreasurer(conn, username, orgName, treasurer)
            if act == "removeTreasurer":
                orgName = request.form['orgName']
                treasurer = request.form['username']
                A.deleteTreasurer(conn, username, orgName, treasurer)
            if act == "addSOFC":
                SOFC = request.form['username']
                A.addSOFC(conn, username, SOFC)
            if act == "removeSOFC":
                SOFC = request.form['username']
                A.deleteSOFC(conn, username, SOFC)
            return render_template('adminUsers.html',
                                   username=username)
    else:
        return redirect(url_for('login'))

# admin orgs display
@app.route('/adminOrgs/')
def displayAdminOrgs():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        orgList = G.allOrgs(conn)
        if admin:
            return render_template('adminOrgs.html',
                                   username=username,
                                   orgList=orgList)
    else:
        return redirect(url_for('login'))

# admin orgs route
@app.route('/adminOrgs/', methods=['POST'])
def adminOrgs():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        if admin:
            act = request.form['submit']
            if act == "addOrg":
                name = request.form['name']
                classification = request.form['classification']
                sofc = request.form['sofc']
                profit = request.form['profit']
                A.addOrg(conn, username, name, classification, sofc, profit)
            if act == "":
                pass
            return render_template('adminOrgs.html',
                                   username=username,
                                   orgList=orgList)
    else:
        return redirect(url_for('login'))

# admin users display
@app.route('/adminDeadlines/')
def displayAdminDeadlines():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        deadlineList = G.allDeadlines(conn)
        if admin:
            return render_template('adminDeadlines.html',
                                   username=username,
                                   deadlineList=deadlineList)
    else:
        return redirect(url_for('login'))

# admin users route
@app.route('/adminDeadlines/', methods=['POST'])
def adminDeadlines():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        if admin:
            act = request.form['submit']
            if act == "grantDeadline":
                deadline = request.form['deadline']
                A.calcAllocated(conn, deadline)
            if act == "addDeadline":
                fType = request.form['fType']
                deadline = request.form['deadline']
                appealsDeadline = request.form['appealsDeadline']
                budgetFood = request.form['budgetFood']
                budgetNonFood = request.form['budgetNonFood']
                A.addDeadline(conn, username, deadline, fType, budgetFood,
                              budgetNonFood)
            if act == "delete":
                deadline = request.form['deadline']
                A.deleteDeadline(conn, username, deadline)
            deadlineList = G.allDeadlines(conn)
            return render_template('adminDeadlines.html',
                                   username=username,
                                   deadlineList=deadlineList)
    else:
        return redirect(url_for('login'))
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = 1947
    DSN = dbconn2.read_cnf()
    DSN['db'] = db
    app.debug = True
    app.run('0.0.0.0',port)
