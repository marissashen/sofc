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
                  WHERE  username=%s',
                 [username])
    info = curs.fetchall()
    return info

# returns name of org given sofc
def orgSOFC(conn, sofc):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT name FROM org WHERE sofc=%s',
                 [sofc])
    info = curs.fetchone()
    orgName = info['name']
    return orgName

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

# return all events for an org
def ownEvents(conn, orgName, date):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * \
                  FROM   event \
                  WHERE  orgName=%s \
                         AND %s<fundingDeadline \
                  ORDER  BY eventName',
                 [orgName, date])
    info = curs.fetchall()
    return info

# add new event
def addEvent(conn, username, orgName, eventName, eventDate, fundingDeadline,
             eType, students):
    # check if user is treaurer of org creating event for
    if isTreasurerOrg(conn, username, orgName):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)

        # check another event with same name hasn't been made already
        if dupName(conn, orgName, eventName, fundingDeadline):
            return "An event with the name "+eventName+" has already been \
                   submitted. Please use another name."

        # add event
        curs.execute('INSERT INTO event \
                                  (treasurer, orgName, eventName, eventDate, \
                                   fundingDeadline, eType, students) \
                      VALUES      (%s, %s, %s, %s, %s, %s)',
                     [username, orgName, eventName, eventDate, fundingDeadline,
                      eType, students])
        return "Event successfully added. Please add appropriate event costs."

    else:
        return "You are not listed as a treasurer for "+orgName+". Please \
               contact bursarsoffice@wellesley.edu if this is a mistake."

# delete event
def deleteEvent(conn, username, orgName, id):
    if isTreasurerOrg(conn, username, orgName):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('DELETE FROM event WHERE id=%s', [id])
        return "Event successfully deleted."
    else:
        return "You are not listed as a treasurer for "+orgName+". Please \
               contact bursarsoffice@wellesley.edu if this is a mistake."

# update event
def updateEvent(conn, username, id, orgName, eventName, eventDate,
                fundingDeadline, eType, students, foodReq, nonFoodReq):
    # check if user is treaurer of org
    if isTreasurerOrg(conn, username, orgName):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)

        # check another event with same name hasn't been made already
        curs.execute('SELECT * \
                      FROM   event \
                      WHERE  orgName=%s \
                             AND eventName=%s \
                             AND fundingDeadline=%s',
                     [orgName, eventName, fundingDeadline])
        info = curs.fetchone()
        if info is None:
            return "The event you are trying to update does not exist."

        # add event
        curs.execute('UPDATE event \
                      SET    treasurer=%s, \
                             eventName=%s, \
                             eventDate=%s, \
                             fundingDeadline=%s, \
                             eType=%s, \
                             students=%s, \
                             foodReq=%s, \
                             nonFoodReq=%s \
                      WHERE id=%s',
                     [username, eventName, eventDate, fundingDeadline, eType,
                     students, foodReq, nonFoodReq, id])
        return "Event successfully updated. Please add appropriate event costs."

    else:
        return "You are not listed as a treasurer for "+orgName+". Please \
               contact bursarsoffice@wellesley.edu if this is a mistake."

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

# add cost
# args is a list of parameters specific for what type of cost is being added
def addCost(conn, username, orgName, eventID, total, cType, args):
    if isTreasurerOrg(conn, username, orgName):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('START TRANSACTION')
        curs.execute('INSERT INTO cost \
                                  (eventID, treasurer, total, cType) \
                      VALUES      (%s, %s, %s, %s)',
                     [eventID, username, total, cType])
        curs.execute('SELECT last_insert_id()')
        info = curs.fetchone()
        id = info['last_insert_id()']

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
                curs.execute('INSERT INTO formula \
                                          (id, kind, input, output, pdf) \
                              VALUES      (%s, %s, %s, %s, %s)',
                             [id, kind, input, output, pdf])
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
                                          (id, pdf1, pdf2, pdf3) \
                              VALUES      (%s, %s, %s, %s)',
                             [id, pdf1, pdf2, pdf3])
                curs.execute('COMMIT')
                return cType+" successfully added."
            else:
                curs.execute('ROLLBACK')
                return "Was unable to add what you submitted."

    else:
        return "You are not listed as a treasurer for "+orgName+". Please \
               contact bursarsoffice@wellesley.edu if this is a mistake."

# delete cost
def deleteCost(conn, username, orgName, id):
    if isTreasurerOrg(conn, username, orgName):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)

        # remove indiv cost from event total cost (food or non food)
        curs.execute('SELECT * FROM cost WHERE id=%s', [id])
        info = curs.fetchone()
        eventID = info['eventID']
        total = info['total']
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
    else:
        return "You are not listed as a treasurer for "+orgName+". Please \
               contact bursarsoffice@wellesley.edu if this is a mistake."

# update cost
def updateCost(conn, username, orgName, id, total, args):
    if isTreasurerOrg(conn, username, orgName):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('START TRANSACTION')

        # adjust event total cost via diff between old indiv cost & new
        curs.execute('SELECT * FROM cost WHERE id=%s', [id])
        info = curs.fetchone()
        eventID = info['eventID']
        oldTotal = info['total']
        cType = info['cType']
        diff = total-oldTotal

        curs.execute('UPDATE cost \
                      SET    treasurer=%s, \
                             total=%s \
                      WHERE  id=%s',
                     [username, total, id])

        if cType == "Food":
            curs.execute('UPDATE event SET foodReq=foodReq+%s WHERE id=%s',
                         [diff, eventID])
            explanation = args[0]
            curs.execute('UPDATE food SET explanation=%s WHERE id=%s',
                         [explanation, id])
            curs.execute('COMMIT')
            return cType+" successfully updated."

        else:
            curs.execute('UPDATE event \
                          SET    nonFoodReq=nonFoodReq+%s \
                          WHERE  id=%s',
                         [diff, eventID])

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

    else:
        return "You are not listed as a treasurer for "+orgName+". Please \
               contact bursarsoffice@wellesley.edu if this is a mistake."

# add appeal
def addAppeal(conn, username, orgName, id, explanation, pdf):
    if isTreasurerOrg(conn, username, orgName):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('INSERT INTO appeal \
                                  (treasurer, explanation, pdf) \
                      VALUES      (%s, %s, %s, %s)',
                     [username, explanation, pdf])
        return "Appeal successfully added."
    else:
        return "You are not listed as a treasurer for "+orgName+". Please \
               contact bursarsoffice@wellesley.edu if this is a mistake."

# delete appeal
def deleteAppeal(conn, username, orgName, id):
    if isTreasurerOrg(conn, username, orgName):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('DELETE FROM appeal WHERE id=%s', [id])
        return "Appeal successfully deleted."
    else:
        return "You are not listed as a treasurer for "+orgName+". Please \
               contact bursarsoffice@wellesley.edu if this is a mistake."

# update appeal
def updateAppeal(conn, username, orgName, id, explanation, pdf):
    if isTreasurerOrg(conn, username, orgName):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('UPDATE appeal \
                      SET    treasurer=%s, \
                             explanation=%s, \
                             pdf=%s \
                      WHERE id=%s',
                     [username, explanation, pdf, id])
        return "Appeal successfully updated."
    else:
        return "You are not listed as a treasurer for "+orgName+". Please \
               contact bursarsoffice@wellesley.edu if this is a mistake."
