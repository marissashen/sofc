from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug import secure_filename
from flask_cas import CAS

import os
import imghdr
import datetime

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

    role = request.form['submit']
    if role == "GENERAL MEMBER":
        return redirect(url_for('general'))
    if role == "TREASURER":
        return redirect(url_for('treasurer'))
    if role == "SOFC MEMBER":
        return redirect(url_for('sofc'))
    if role == "ADMIN":
        return redirect(url_for('admin'))

# general route
@app.route('/general/')
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
@app.route('/treasurer/')
def displayTreasurer():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        treasurer = T.isTreasurer(conn, username)
        orgs = T.treasurersOrgs(conn, username)
        date = datetime.datetime.now()
        deadline = T.getDeadline(conn, date)
        session['deadline'] = deadline
        if treasurer:
            # go directly to org if user only treasurer for 1 org
            if len(orgs)==1:
                sofc = orgs[1]['sofc']
                return redirect(url_for('treasurerOrg',
                                        sofc=sofc))
            # page where treasurer can pick which org they want to look at
            else:
                return render_template('treasurer.html',
                                       username=username,
                                       orgs=orgs)
    else:
        return redirect(url_for('login'))

# treaurer routes
@app.route('/treasurer/', methods=['POST'])
def treasurer():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        sofc = int(request.form['submit'])
        treasurer = T.isTreasurerSOFC(conn, username, sofc)
        if treasurer:
            return redirect(url_for('treasurerOrg',
                                    sofc=sofc))
    else:
        return redirect(url_for('login'))

# display treaurer org
@app.route('/treasurerOrg/<sofc>')
def displayTreasurerOrg(sofc):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        deadline = session['deadline']
        funding = T.getFunding(conn, deadline)
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        if treasurer:
            deadlineList = G.allDeadlines(conn)
            eventList = G.allEventsNow(conn, orgName, deadline)
            return render_template('treasurerOrg.html',
                                   username=username,
                                   funding=funding,
                                   deadlineList=deadlineList,
                                   eventList=eventList)
    else:
        return redirect(url_for('login'))

# treaurer org routes
@app.route('/treasurerOrg/<sofc>', methods=['POST'])
def treasurerOrg(sofc):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        deadline = session['deadline']
        funding = T.getFunding(conn, deadline)
        if treasurer:
            act = request.form['submit']

            # edit event (also add costs & appeals)
            if act[:4] == "edit":
                eventID = int(act[5:])
                return redirect(url_for('treasurerEvent',
                                        sofc=sofc,
                                        eventID=eventID))
            # pureposefully change deadline
            if act == "change":
                fundingDeadline = request.form['fundingDeadline']
                session['deadline'] = fundingDeadline
            # add a new event
            if act == "event":
                fundingDeadline = funding['deadline']
                eventName = request.form['eventName']
                purpose = request.form['purpose']
                eType = request.form['eType']
                eventDate = request.form['eventDate']
                students = request.form['students']
                T.addEvent(conn, username, orgName, eventName purpose,
                           eventDate, fundingDeadline, eType, students)
            return displayTreasurerOrg(sofc)
    else:
        return redirect(url_for('login'))

# display treaurer event
@app.route('/treasurerEvent/<sofc>-<eventID>')
def displayTreasurerEvent(sofc, eventID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        if treasurer:
            event = G.eventInfo(conn, eventID)
            costList = G.eventCosts(conn, eventID)
            costAppealList = G.eventCostsAppeals(conn, eventID)
            return render_template('treasurerEvent.html',
                                   event=event,
                                   costList=costList,
                                   costAppealList=costAppealList)
    else:
        return redirect(url_for('login'))

# treaurer event routes
@app.route('/treasurerEvent/<sofc>-<eventID>', methods=['POST'])
def treasurerEvent(sofc, eventID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        deadline = session['deadline']
        if treasurer:
            act = request.form['submit']

            # update event
            if act == "update":
                eventName = request.form['eventName']
                purpose = request.form['purpose']
                eType = request.form['eType']
                eventDate = request.form['eventDate']
                students = request.form['students']
                eventID = int(eventID)
                T.updateEvent(conn, username, eventID, orgName, eventName,
                              purpose, eventDate, deadline, eType, students)
                return displayTreasurerEvent(sofc, eventID)
            # delete event
            if act == "delete":
                T.deleteEvent(conn, orgName, eventID)
                return redirect(url_for('treasurerOrg',
                                        sofc=sofc))
            # add a new cost to an existing event
            if act == "cost":
                eventID = request.form['eventID']
                return redirect(url_for('treasurerCost',
                                        eventID=eventID))
            # edit an existing cost
            if act[:3] == "edc":
                costID = int(act[4:])
                return redirect(url_for('treasurerUpdateCost',
                                        costID=costID))
            # add a new appeal to an existing cost
            if act[:3] == "add":
                costID = int(act[4:])
                return redirect(url_for('treasurerAppeal',
                                        sofc=sofc,
                                        costID=costID))
            # edit an existing appeal
            if act[:3] == "eda":
                costID = int(act[4:])
                return redirect(url_for('treasurerUpdateAppeal',
                                        sofc=sofc,
                                        costID=costID))
    else:
        return redirect(url_for('login'))

# display treaurer cost
@app.route('/treasurerCost/<eventID>')
def displayTreasurerCost(eventID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        pass
        if treasurer:
            pass
            eventName = T.getName(conn, eventID)
            return render_template('treasurerCost.html',
                                   eventName=eventName)
    else:
        return redirect(url_for('login'))

# treaurer cost routes
@app.route('/treasurerCost/<eventID>', methods=['POST'])
def treasurerCost(eventID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        pass
        if treasurer:
            if request.form['submit'] == "add":
                cType = request.form['cType']
                args = request.form['args']
                total = request.form['total']
                T.addCost(conn, username, orgName, eventID, total, cType, args)
                pass
                return
    else:
        return redirect(url_for('login'))

# display treaurer appeal
@app.route('/treasurerAppeal/<sofc>-<costID>')
def displayTreasurerAppeal(sofc, costID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        if treasurer:
            (eventName, cType) = T.getNameCType(conn, costID)
            return render_template('treasurerAppeal.html',
                                   eventName=eventName,
                                   cType=cType)
    else:
        return redirect(url_for('login'))

# treaurer appeal routes
@app.route('/treasurerAppeal/<sofc>-<costID>', methods=['POST'])
def treasurerAppeal(sofc, costID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        if treasurer:
            if request.form['submit'] == "add":
                explanation = request.form['explanation']
                pdf = request.form['pdf']
                T.addAppeal(conn, username, orgName, costID, explanation, pdf)
                return
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
            # possible pages to go to
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
def displayAdminUsers():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        sofcOrgList = G.allSOFCOrgs(conn)
        if admin:
            return render_template('adminUsers.html',
                                   username=username,
                                   sofcOrgList=sofcOrgList)
    else:
        return redirect(url_for('login'))

# admin users route
@app.route('/adminUsers/', methods=['POST'])
def adminUsers():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        if admin:
            act = request.form['submit']
            # adding a new treasurer
            if act == "addTreasurer":
                orgName = request.form['orgName']
                treasurer = request.form['username']
                A.addTreasurer(conn, orgName, treasurer)
            # removing user from being an treasurer
            if act == "removeTreasurer":
                orgName = request.form['orgName']
                treasurer = request.form['username']
                A.deleteTreasurer(conn, orgName, treasurer)
            # adding user to sofc group
            if act == "addSOFC":
                SOFC = request.form['username']
                A.addSOFC(conn, SOFC)
            # removing user from sofc group
            if act == "removeSOFC":
                SOFC = request.form['username']
                A.deleteSOFC(conn, SOFC)
            return displayAdminUsers()
    else:
        return redirect(url_for('login'))

# admin orgs display
@app.route('/adminOrgs/')
def displayAdminOrgs():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        sofcOrgList = G.allSOFCOrgs(conn)
        orgList = G.allOrgs(conn)
        if admin:
            return render_template('adminOrgs.html',
                                   username=username,
                                   sofcOrgList=sofcOrgList,
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
        orgList = G.allOrgs(conn)
        if admin:
            act = request.form['submit']
            # adding a new org for sofc funding
            if act == "add":
                name = request.form['name']
                classification = request.form['classification']
                sofc = request.form['sofc']
                profit = request.form['profit']
                A.addOrg(conn, name, classification, sofc, profit)
            # deleting an org or revoking sofc funding status
            if act == "delete":
                name = request.form['name']
                A.deleteOrg(conn, name)
            # updating org info
            if act == "update":
                sofc = request.form['name']
                return redirect(url_for('displayUpdateOrg',
                                        sofc=sofc))
            return displayAdminOrgs()
    else:
        return redirect(url_for('login'))

# admin org update display
@app.route('/adminUpdateOrg/<sofc>')
def displayUpdateOrg(sofc):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        info = G.orgInfo(conn, sofc)
        if info['canApply']==0:
            canApply = False
        else:
            canApply = True
        if admin:
            return render_template('adminOrgInfo.html',
                                   info=info,
                                   canApply=canApply)
    else:
        return redirect(url_for('login'))

# admin org update route
@app.route('/adminUpdateOrg/<sofc>', methods=['POST'])
def updateOrg(sofc):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        admin = A.isAdmin(conn, username)
        oldName = A.orgName(conn, sofc)
        if admin:
            newName = request.form['name']
            classification = request.form['classification']
            newSOFC = request.form['sofc']
            profit = request.form['profit']
            canApply = int(request.form['canApply'])
            A.updateOrg(conn, oldName, newName, classification, sofc, newSOFC,
                        profit, canApply)
            return displayUpdateOrg(sofc)
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
            # allocate funds for deadline
            if act == "allocateDeadline":
                deadline = request.form['deadline']
                A.calcAllocated(conn, deadline)
            # creating new deadline
            if act == "addDeadline":
                fType = request.form['fType']
                deadline = request.form['deadline']
                appealsDeadline = request.form['appealsDeadline']
                budgetFood = request.form['budgetFood']
                budgetNonFood = request.form['budgetNonFood']
                A.addDeadline(conn, deadline, fType, budgetFood,
                              budgetNonFood)
            # deleting deadline
            if act == "delete":
                deadline = request.form['deadline']
                A.deleteDeadline(conn, deadline)
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
