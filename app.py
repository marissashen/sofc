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
                sofc = orgs[0]['sofc']
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
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            deadlineList = G.allDeadlines(conn)
            eventList = G.allEventsNow(conn, orgName, deadline)
            return render_template('treasurerOrg.html',
                                   canEdit=canEdit,
                                   username=username,
                                   orgName=orgName,
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
        deadline = session['deadline']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        funding = T.getFunding(conn, deadline)
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            act = request.form['submit']

            # edit event (also add costs & appeals)
            if act[:4] == "edit":
                eventID = int(act[5:])
                return redirect(url_for('treasurerEvent',
                                        sofc=sofc,
                                        eventID=eventID))
            # purposefully change deadline
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
                message = T.addEvent(conn, username, orgName, eventName,
                                     purpose, eventDate, fundingDeadline, eType,
                                     students)
                if message[0:2] == "An":
                    pass
            return displayTreasurerOrg(sofc)
    else:
        return redirect(url_for('login'))

# display treaurer event
@app.route('/treasurerEvent/<sofc>-<eventID>')
def displayTreasurerEvent(sofc, eventID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        deadline = session['deadline']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            event = G.eventInfo(conn, eventID)
            costList = G.eventCosts(conn, eventID)
            costAppealList = G.eventCostsAppeals(conn, eventID)
            return render_template('treasurerEvent.html',
                                   canEdit=canEdit,
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
        deadline = session['deadline']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            sofc = int(sofc)
            eventID = int(eventID)
            oldEventName = T.getName(conn, eventID)
            act = request.form['submit']

            # update event
            if act == "update":
                eventName = request.form['eventName']
                purpose = request.form['purpose']
                eType = request.form['eType']
                eventDate = request.form['eventDate']
                students = request.form['students']
                T.updateEvent(conn, username, eventID, orgName, oldEventName,
                              eventName, purpose, eventDate, deadline, eType,
                              students)
                return displayTreasurerEvent(sofc, eventID)
            # delete event
            elif act == "delete":
                T.deleteEvent(conn, orgName, eventID)
                return redirect(url_for('treasurerOrg',
                                        sofc=sofc))
            # add a new cost to an existing event
            elif act == "cost":
                return redirect(url_for('treasurerCost',
                                        sofc=sofc,
                                        eventID=eventID))
            # edit an existing cost
            elif act[:3] == "edc":
                costID = int(act[4:])
                return redirect(url_for('treasurerUpdateCost',
                                        sofc=sofc,
                                        eventID=eventID,
                                        costID=costID,))
            # add a new appeal to an existing cost
            elif act[:3] == "add":
                costID = int(act[4:])
                return redirect(url_for('treasurerAppeal',
                                        sofc=sofc,
                                        costID=costID))
            # edit an existing appeal
            elif act[:3] == "eda":
                costID = int(act[4:])
                return redirect(url_for('treasurerUpdateAppeal',
                                        sofc=sofc,
                                        costID=costID))
    else:
        return redirect(url_for('login'))

# display treaurer cost
@app.route('/treasurerCost/<sofc>-<eventID>')
def displayTreasurerCost(sofc, eventID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        deadline = session['deadline']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            sofc = int(sofc)
            eventName = T.getName(conn, eventID)
            return render_template('treasurerCost.html',
                                   canEdit=canEdit,
                                   eventName=eventName)
    else:
        return redirect(url_for('login'))

# treaurer cost routes
@app.route('/treasurerCost/<sofc>-<eventID>', methods=['POST'])
def treasurerCost(sofc, eventID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        deadline = session['deadline']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            eventID = int(eventID)
            if request.form['submit'] == "add":
                total = request.form['total']
                cType = request.form['cType']
                costID = T.addCost1(conn, username, eventID, total, cType)
                if cType == "Attendee":
                    pdf = request.files['pdf']
                    filename = secure_filename(str(costID)+".pdf")
                    pathname = "files/"+filename
                    pdf.save(pathname)
                    args = [pathname]
                elif cType == "Food":
                    explanation = request.form['explanation']
                    args = [explanation]
                elif cType == "Formula":
                    kind = request.form['kind']
                    input = request.form['input']
                    pdf = request.form.get('pdf', None)
                    pathname = None
                    if pdf:
                        filename = secure_filename(str(costID)+".pdf")
                        pathname = "files/"+filename
                        pdf.save(pathname)
                    args = [kind, input, None]
                elif cType == "Honorarium":
                    name = request.form['name']
                    contract = request.files['contract']
                    args = [name, contract]
                elif cType == "Supply":
                    pdf1 = request.files['pdf1']
                    filename1 = secure_filename(str(costID)+"pdf1.pdf")
                    pathname1 = "files/"+filename1
                    pdf1.save(pathname1)
                    pathname2 = None
                    pathname3 = None
                    pdf2 = request.form.get('pdf2', None)
                    if pdf2:
                        filename2 = secure_filename(str(costID)+"pdf2.pdf")
                        pathname2 = "files/"+filename2
                        pdf.save(pathname2)
                    pdf3 = request.form.get('pdf3', None)
                    if pdf3:
                        filename3 = secure_filename(str(costID)+"pdf3.pdf")
                        pathname3 = "files/"+filename3
                        pdf.save(pathname3)
                    args = [pathname1, pathname2, pathname3]
                T.addCost2(conn, costID, cType, args)
                return redirect(url_for('displayTreasurerEvent',
                                        sofc=sofc,
                                        eventID=eventID))
    else:
        return redirect(url_for('login'))

# display update treaurer cost
@app.route('/treasurerUpdateCost/<sofc>-<eventID>-<costID>')
def displayTreasurerUpdateCost(sofc, eventID, costID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        deadline = session['deadline']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            sofc = int(sofc)
            costID = int(costID)
            eventID = int(eventID)
            general, specific = T.getCost(conn, costID)
            eventName = T.getName(conn, eventID)
            return render_template('treasurerUpdateCost.html',
                                   canEdit=canEdit,
                                   general=general,
                                   specific=specific,
                                   eventName=eventName)
    else:
        return redirect(url_for('login'))

# update treaurer cost routes
@app.route('/treasurerUpdateCost/<sofc>-<eventID>-<costID>', methods=['POST'])
def treasurerUpdateCost(sofc, eventID, costID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        deadline = session['deadline']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            costID = int(costID)
            eventID = int(eventID)
            act = request.form['submit']
            if act == "update":
                total = request.form['total']
                if cType == "Attendee":
                    pdf = request.form['pdf']
                    args = [pdf]
                elif cType == "Food":
                    explanation = request.form['explanation']
                    args = [explanation]
                elif cType == "Formula":
                    kind = request.form['kind']
                    input = request.form['input']
                    pdf = request.form['pdf']
                    args = [kind, input, pdf]
                elif cType == "Honorarium":
                    name = request.form['name']
                    contract = request.form['contract']
                    args = [name, contract]
                elif cType == "Supply":
                    pdf1 = request.form['pdf1']
                    pdf2 = request.form['pdf2']
                    pdf3 = request.form['pdf3']
                    args = [pdf1, pdf2, pdf3]
                T.updateCost(conn, username, costID, total, args)
            elif act == "delete":
                T.deleteCost(conn, username, costID)
            return redirect(url_for('treasurerEvent',
                                    sofc=sofc,
                                    eventID=eventID))
    else:
        return redirect(url_for('login'))

# display treaurer appeal
@app.route('/treasurerAppeal/<sofc>-<costID>')
def displayTreasurerAppeal(sofc, costID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        deadline = session['deadline']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            (eventName, cType) = T.getNameCType(conn, costID)
            return render_template('treasurerAppeal.html',
                                   canEdit=canEdit,
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
        deadline = session['deadline']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            costID = int(costID)
            if request.form['submit'] == "add":
                explanation = request.form['explanation']
                pdf = request.form.get('pdf', None)
                T.addAppeal(conn, username, costID, explanation, pdf)
                eventID = T.getEventID(conn, costID)
                return redirect(url_for('treasurerEvent',
                                        sofc=sofc,
                                        eventID=eventID))
    else:
        return redirect(url_for('login'))

# display update treaurer appeal
@app.route('/treasurerUpdateAppeal/<sofc>-<costID>')
def displayTreasurerUpdateAppeal(sofc, costID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        deadline = session['deadline']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            costID = int(costID)
            info = T.getNameCTypeUpdate(conn, costID)
            return render_template('treasurerUpdateAppeal.html',
                                   canEdit=canEdit,
                                   info=info)
    else:
        return redirect(url_for('login'))

# treaurer update appeal routes
@app.route('/treasurerUpdateAppeal/<sofc>-<costID>', methods=['POST'])
def treasurerUpdateAppeal(sofc, costID):
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        deadline = session['deadline']
        orgName = T.orgSOFC(conn, sofc)
        treasurer = T.isTreasurerOrg(conn, username, orgName)
        date = datetime.datetime.now()
        canEdit = date<=deadline
        if treasurer:
            costID = int(costID)
            eventID = T.getEventID(conn, costID)
            act = request.form['submit']
            if act == "update":
                explanation = request.form['explanation']
                pdf = request.form.get('pdf', None)
                T.updateAppeal(conn, username, costID, explanation, pdf)
            elif act == "delete":
                T.deleteAppeal(conn, username, costID)
                eventID = T.getEventID(conn, costID)
            return redirect(url_for('treasurerEvent',
                                    sofc=sofc,
                                    eventID=eventID))
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
                profit = request.form.get('profit', None)
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
            profit = request.form.get('profit', None)
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
