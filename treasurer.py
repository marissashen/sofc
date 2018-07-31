#!/usr/local/bin/python2.7

import sys
import MySQLdb
import dbconn2

# ------------------------------------------------------------------------------

# check if user is treasurer of any org
def isTreasurer(conn, username):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * FROM treasurer WHERE username=%s', [username])
    info = curs.fetchone()
    return info is not None

# check if user is treasurer of org (can create/update event & event costs)
def isTreasurerOrg(conn, username, orgName):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * \
                  FROM   treasurer \
                  WHERE  username=%s \
                         AND orgName=%s',
                 [username, orgName])
    info = curs.fetchone()
    return info is not None

# check if user is treasurer of sofc
def isTreasurerSOFC(conn, username, sofc):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * \
                  FROM   treasurer, org \
                  WHERE  username=%s \
                         AND sofc=%s',
                 [username, sofc])
    info = curs.fetchone()
    return info is not None

# return all orgs user is treasurer of along w. sofc nums
def treasurersOrgs(conn, username):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT orgName, sofc \
                  FROM   treasurer, org \
                  WHERE  username=%s \
                         AND orgName=name',
                 [username])
    info = curs.fetchall()
    return info

# return name of org given sofc
def orgSOFC(conn, sofc):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT name FROM org WHERE sofc=%s',
                 [sofc])
    info = curs.fetchone()
    orgName = info['name']
    return orgName

# return name of event given event id
def getName(conn, eventID):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT eventName FROM event WHERE id=%s',
                 [eventID])
    info = curs.fetchone()
    eventName = info['eventName']
    return eventName

# get all cost info given id (general info, cost type specific info)
def getCost(conn, costID):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * FROM cost WHERE id=%s',
                 [costID])
    general = curs.fetchone()
    cType = general['cType'].lower()
    sql = "SELECT * FROM "+cType+" WHERE id=%s"
    curs.execute(sql, [costID])
    specific = curs.fetchone()
    return (general, specific)

# return name of event given cost id
def getNameCTypeUpdate(conn, costID):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT eventName, cType, appeal.*  \
                  FROM   event, cost, appeal \
                  WHERE  cost.id=%s \
                         AND cost.eventID=event.ID \
                         AND appeal.id=%s',
                 [costID, costID])
    info = curs.fetchone()
    return info

# return deadline closest to given current date
def getDeadline(conn, date):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT   deadline \
                  FROM     funding \
                  WHERE    deadline>=%s \
                  ORDER BY deadline ASC',
                 [date])
    info = curs.fetchone()
    deadline = info['deadline']
    return deadline

# return all funding info given deadline
def getFunding(conn, deadline):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * FROM funding WHERE deadline=%s',
                 [deadline])
    info = curs.fetchone()
    return info

# get event id of a cost
def getEventID(conn, costID):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT eventID FROM cost WHERE id=%s',
                 [costID])
    info = curs.fetchone()
    eventID = info['eventID']
    return eventID

# check if event name already exists for org in this deadline
def dupName(conn, orgName, eventName, fundingDeadline):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * \
                  FROM   event \
                  WHERE  orgName=%s \
                         AND eventName=%s \
                         AND fundingDeadline=%s',
                 [orgName, eventName, fundingDeadline])
    info = curs.fetchone()
    return info is not None

# add new event
def addEvent(conn, username, orgName, eventName, purpose, eventDate, fundingDeadline,
             eType, students):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)

    # check another event with same name hasn't been made already
    if dupName(conn, orgName, eventName, fundingDeadline):
        return "An event with the name "+eventName+" has already been \
               submitted. Please use another name."

    # add event
    curs.execute('INSERT INTO event \
                              (treasurer, orgName, eventName, purpose, \
                               eventDate, fundingDeadline, eType, students) \
                  VALUES      (%s, %s, %s, %s, %s, %s, %s, %s)',
                 [username, orgName, eventName, purpose, eventDate,
                  fundingDeadline, eType, students])
    return "Event successfully added. Please add appropriate event costs."

# delete event
def deleteEvent(conn, orgName, id):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('DELETE FROM event WHERE id=%s', [id])
    return "Event successfully deleted."

# update event
def updateEvent(conn, username, id, orgName, oldEventName, newEventName,
                purpose, eventDate, fundingDeadline, eType, students):

    curs = conn.cursor(MySQLdb.cursors.DictCursor)

    if oldEventName==newEventName:
        # check another event with same name hasn't been made already
        curs.execute('SELECT * \
                      FROM   event \
                      WHERE  orgName=%s \
                             AND eventName=%s \
                             AND fundingDeadline=%s',
                     [orgName, eventName, fundingDeadline])
        info = curs.fetchone()
        if info is not None:
            return "This event name already exists for this deadline."

    else:
        # add event
        curs.execute('UPDATE event \
                      SET    treasurer=%s, \
                             eventName=%s, \
                             purpose=%s, \
                             eventDate=%s, \
                             fundingDeadline=%s, \
                             eType=%s, \
                             students=%s \
                      WHERE  id=%s',
                     [username, eventName, purpose, eventDate, fundingDeadline,
                      eType, students, id])
        return "Event successfully updated. Please add appropriate event costs."

# return cost given formula being used & input
def applyFormula(kind, input):
    if input == 0:
        return 0.00

    if kind == "car":
        return input*0.54
    elif kind == "crowd control":
        return min(input*50.00, 200.00)
    elif kind == "custodial":
        return min((input+2)*35.00, 210.00)
    elif kind == "eboard":
        return input*10.00
    elif kind == "open meeting":
        return 25.00
    elif kind == "programs":
        return min(input*0.10, 25.00)
    elif kind == "publicity":
        return min(input*0.10, 5.00)
    elif kind == "speaker meal":
        return input*15.00

# add cost part 1
# need to get cost id of new cost for pdf naming
def addCost1(conn, username, eventID, total, cType):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('START TRANSACTION')
    curs.execute('INSERT INTO cost \
                              (eventID, treasurer, totalReq, cType) \
                  VALUES      (%s, %s, %s, %s)',
                 [eventID, username, total, cType])
    curs.execute('SELECT last_insert_id()')
    info = curs.fetchone()
    id = info['last_insert_id()']
    return costID

# add cost part 2
# args is a list of parameters specific for what type of cost is being added
def addCost2(conn, costID, cType, args):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    # diff types of costs being added
    # also add indiv cost total to event total cost (food or non food)
    if cType == "Food":
        explanation = args[0]
        curs.execute('INSERT INTO food \
                                  (id, explanation) \
                      VALUES      (%s, %s)',
                     [id, explanation])
        curs.execute('UPDATE event \
                      SET    foodReq=foodReq+%s \
                      WHERE  id=%s',
                     [total, eventID])
        curs.execute('COMMIT')
        return cType+" successfully added."
    else:
        curs.execute('UPDATE event \
                      SET    nonFoodReq=nonFoodReq+%s \
                      WHERE  id=%s',
                     [total, eventID])
        if cType == "Attendee":
            pdf = args[0]
            curs.execute('INSERT INTO attendee \
                                      (id, pdf) \
                          VALUES      (%s, %s)',
                         [id, pdf])
            curs.execute('COMMIT')
            return cType+" successfully added."
        elif cType == "Formula":
            kind, input, pdf = args
            output = applyFormula(kind, input)
            if pdf:
                curs.execute('INSERT INTO formula \
                                          (id, kind, input, output, pdf) \
                              VALUES      (%s, %s, %s, %s, %s)',
                             [id, kind, input, output, pdf])
            else:
                curs.execute('INSERT INTO formula \
                                          (id, kind, input, output) \
                              VALUES      (%s, %s, %s, %s)',
                             [id, kind, input, output])
            curs.execute('COMMIT')
            return cType+" successfully added."
        elif cType == "Honorarium":
            name, contract =  args
            curs.execute('INSERT INTO honorarium \
                                      (id, name, contract) \
                          VALUES      (%s, %s, %s)',
                         [id, name, contract])
            curs.execute('COMMIT')
            return cType+" successfully added."
        elif cType == "Supply":
            pdf1, pdf2, pdf3 = args
            curs.execute('INSERT INTO supply \
                                      (id, pdf1) \
                          VALUES      (%s, %s)',
                         [id, pdf1])
            if pdf2:
                curs.execute('UPDATE supply \
                              SET    pdf2=%s \
                              WHERE  id=%s',
                             [pdf2, id])
            if pdf3:
                curs.execute('UPDATE supply \
                              SET    pdf3=%s \
                              WHERE  id=%s',
                             [pdf3, id])
            curs.execute('COMMIT')
            return cType+" successfully added."
        else:
            curs.execute('ROLLBACK')
            return "Was unable to add what you submitted."

# delete cost
def deleteCost(conn, username, id):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)

    # remove indiv cost from event total cost (food or non food)
    curs.execute('SELECT * FROM cost WHERE id=%s', [id])
    info = curs.fetchone()
    eventID = info['eventID']
    total = info['totalReq']
    cType = info['cType']
    if cType == "Food":
        curs.execute('UPDATE event \
                      SET    foodReq=foodReq-%s \
                      WHERE  id=%s',
                     [total, eventID])
    else:
        curs.execute('UPDATE event \
                      SET    nonFoodReq=nonFoodReq-%s \
                      WHERE  id=%s',
                     [total, eventID])

    curs.execute('DELETE FROM cost WHERE id=%s', [id])
    return "Cost successfully deleted."

# update cost
def updateCost(conn, username, id, total, args):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('START TRANSACTION')

    # adjust event total cost via diff between old indiv cost & new
    curs.execute('SELECT * FROM cost WHERE id=%s', [id])
    info = curs.fetchone()
    eventID = info['eventID']
    oldTotal = info['totalReq']
    cType = info['cType']

    curs.execute('UPDATE cost \
                  SET    treasurer=%s, \
                         totalReq=%s \
                  WHERE  id=%s',
                 [username, total, id])

    if cType == "Food":
        curs.execute('UPDATE event SET foodReq=foodReq+%s-%s WHERE id=%s',
                     [total, oldTotal, eventID])
        explanation = args[0]
        curs.execute('UPDATE food SET explanation=%s WHERE id=%s',
                     [explanation, id])
        curs.execute('COMMIT')
        return cType+" successfully updated."

    else:
        curs.execute('UPDATE event \
                      SET    nonFoodReq=nonFoodReq+%s-%s \
                      WHERE  id=%s',
                     [total, oldTotal, eventID])

        if cType == "Attendee":
            pdf = args[0]
            curs.execute('UPDATE attendee SET pdf=%s WHERE id=%s',
                         [pdf, id])
            curs.execute('COMMIT')
            return cType+" successfully updated."
        elif cType == "Formula":
            kind, input, pdf = args
            output = applyFormula(kind, input)
            curs.execute('UPDATE formula \
                          SET    kind=%s, \
                                 input=%s, \
                                 output=%s \
                                 pdf=%s \
                          WHERE  id=%s',
                         [kind, input, output, pdf, id])
            curs.execute('COMMIT')
            return cType+" successfully updated."
        elif cType == "Honorarium":
            name, contract =  args
            curs.execute('UPDATE honorarium \
                          SET    name=%s, \
                                 contract=%s \
                          WHERE  id=%s',
                         [name, contract, id])
            curs.execute('COMMIT')
            return cType+" successfully updated."
        elif cType == "Supply":
            pdf1, pdf2, pdf3 = args
            curs.execute('UPDATE supply \
                          SET    pdf1=%s, \
                                 pdf2=%s, \
                                 pdf3=%s \
                          WHERE id=%s',
                         [pdf1, pdf2, pdf3, id])
            curs.execute('COMMIT')
            return cType+" successfully updated."
        else:
            curs.execute('ROLLBACK')
            return "Was unable to update what you submitted."

# add appeal
def addAppeal(conn, username, id, explanation, pdf):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    if pdf:
        curs.execute('INSERT INTO appeal \
                                  (id, treasurer, explanation, pdf) \
                      VALUES      (%s, %s, %s, %s)',
                     [id, username, explanation, pdf])
    else:
        curs.execute('INSERT INTO appeal \
                                  (id, treasurer, explanation) \
                      VALUES      (%s, %s, %s)',
                      [id, username, explanation])
    return "Appeal successfully added."

# delete appeal
def deleteAppeal(conn, username, id):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('DELETE FROM appeal WHERE id=%s', [id])
    return "Appeal successfully deleted."

# update appeal
def updateAppeal(conn, username, id, explanation, pdf):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    if pdf:
        curs.execute('UPDATE appeal \
                      SET    treasurer=%s, \
                             explanation=%s, \
                             pdf=%s \
                      WHERE id=%s',
                     [username, explanation, pdf, id])
    else:
        curs.execute('UPDATE appeal \
                      SET    treasurer=%s, \
                             explanation=%s \
                      WHERE  id=%s',
                     [username, explanation, id])
    return "Appeal successfully updated."
