#!/usr/local/bin/python2.7

import sys
import MySQLdb
import dbconn2

# ------------------------------------------------------------------------------

# check if user is admin (can add new users to sofc & create funding deadlines)
def isAdmin(conn, username):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT uType FROM user WHERE username=%s', [username])
    info = curs.fetchone()
    return info['uType'] == "admin"

# add funding deadline
def addDeadline(conn, deadline, fType, budgetFood, budgetNonFood):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('INSERT INTO funding \
                              (deadline, fType, budgetFood, budgetNonFood) \
                  VALUES      (%s, %s, %s, %s)',
                 [deadline, fType, budgetFood, budgetNonFood])
    return "Deadline has been successfully added."

# delete funding deadline
def deleteDeadline(conn, deadline):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('DELETE FROM funding WHERE deadline=%s',
                 [deadline])
    return "Deadline has been successfully deleted."

# add user as a treasurer
def addTreasurer(conn, orgName, treasurer):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('INSERT INTO user \
                              (username) \
                  VALUES      (%s) \
                  ON DUPLICATE KEY UPDATE username=%s',
                 [treasurer, treasurer])
    curs.execute('INSERT INTO treasurer \
                              (orgName, username) \
                  VALUES      (%s, %s) \
                  ON DUPLICATE KEY UPDATE username=%s',
                 [orgName, treasurer, treasurer])
    return "Treasurer "+treasurer+" for "+orgName+" has been successfully \
            added."

# delete user as a treasurer
def deleteTreasurer(conn, orgName, treasurer):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('DELETE FROM treasurer \
                  WHERE       orgName=%s \
                              AND username=%s',
                 [orgName, treasurer])
    return "Treasurer "+treasurer+" for "+orgName+" has been successfully \
           deleted."

# add user as a SOFC member
def addSOFC(conn, SOFC):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT uType FROM user WHERE username=%s',
                 [SOFC])
    info = curs.fetchone()
    if info is None or info['uType'] == "general":
        curs.execute('INSERT INTO user \
                                  (username, uType) \
                      VALUES      (%s, "sofc") \
                      ON DUPLICATE KEY UPDATE uType="sofc"',
                     [SOFC])
    return "SOFC member "+SOFC+" has been successfully added."

# delete user as a SOFC member
def deleteSOFC(conn, SOFC):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT uType FROM user WHERE username=%s',
                 [SOFC])
    info = curs.fetchone()
    if info is None or info['uType'] == "sofc":
        curs.execute('UPDATE user SET uType=1 WHERE username=%s',
                     [SOFC])
    return "SOFC member "+SOFC+" has been successfully deleted."

# add new org
def addOrg(conn, name, classification, sofc, profit):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('INSERT INTO org \
                              (name, classification, sofc) \
                  VALUES      (%s, %s, %s)',
                 [name, classification, sofc])
    if profit:
        curs.execute('UPDATE org \
                      SET    profit=%s \
                      WHERE  name=%s',
                     [profit, name])
    return "Org "+name+" has been successfully added."

# remove org's ability to apply for sofc (or delete if never applied before)
def deleteOrg(conn, name):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * FROM event WHERE orgName=%s',
                 [name])
    info = curs.fetchone()
    if info is None:
        curs.execute('DELETE FROM org WHERE name=%s',
                     [name])
        return "Org "+name+"has been successfully deleted."
    curs.execute('UPDATE org \
                  SET    canApply=FALSE \
                  WHERE  name=%s',
                 [name])
    return "Org "+name+" has been successfully removed from SOFC funding."

# update org
def updateOrg(conn, oldName, newName, classification, sofc, profit,
              canApply):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT COUNT(*) FROM org WHERE sofc=%s',
                 [sofc])
    info = curs.fetchone()
    nums = info['COUNT(*)']
    if nums>0:
        return "SOFC number "+sofc+" already belongs to another org."
    curs.execute('UPDATE org \
                  SET    name=%s, \
                         classification=%s, \
                         sofc=%s \
                         canApply=%s \
                  WHERE  name=%s',
                 [newName, classification, sofc, oldName, canApply])
    if profit:
        curs.execute('UPDATE org SET profit=%s WHERE name=%s',
                     [profit, newName])
    return "Org "+name+" has been successfully updated."

# get name of org given sofc num (also unique)
def orgName(conn, sofc):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT name FROM org WHERE sofc=%s',
                 [sofc])
    info = curs.fetchone()
    name = info['name']
    return name

# get sofc num of org given name
def orgSOFC(conn, name):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT sofc FROM org WHERE name=%s',
                 [name])
    info = curs.fetchone()
    sofc = info['sofc']
    return sofc

# return unreviewed costs
def checkCosts(conn, fundingDeadline):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    # want id of unreviewed costs that belong to events for this deadline
    curs.execute('SELECT cost.id \
                  FROM   cost, event \
                  WHERE  cost.reviewed=FALSE \
                         AND cost.eventID=event.id \
                         AND event.fundingDeadline=%s',
                 [fundingDeadline])
    info = curs.fetchall()
    return info

# return unreviewed appeals
def checkAppeals(conn, fundingDeadline):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    # want id of unreviewed appeals
    # appeals need to belong to costs that belong to events for this deadline
    curs.execute('SELECT appeal.id \
                  FROM   appeal, cost, event \
                  WHERE  appeal.reviewed=FALSE \
                         AND appeal.id=cost.id \
                         AND cost.eventID=event.id \
                         AND event.fundingDeadline=%s',
                 [fundingDeadline])
    info = curs.fetchall()
    return info

# check all costs & appeals reviewed
def allReviewed(conn, fundingDeadline):
    unreviewedCosts = checkCosts(conn, fundingDeadline)
    unreviewedAppeals = checkAppeals(conn, fundingDeadline)
    costs = (unreviewedCosts == {})
    appeals = (unreviewedAppeals == {})
    return (costs and appeals)

# recalculate all granted money via costs
def calcGranted(conn, fundingDeadline):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)

    # granted food
    curs.execute('SELECT event.id, \
                         SUM(cost.totalGrant) AS "foodGrant" \
                  FROM   event, cost \
                  WHERE  cost.cType="Food" \
                         AND  cost.eventID=event.id \
                         AND event.fundingDeadline=%s \
                  GROUP  BY event.id',
                 [fundingDeadline])
    grantedFood = curs.fetchall()
    for foodCost in grantedFood:
        id = foodCost['event.id']
        foodGrant = foodCost['foodGrant']
        curs.execute('UPDATE event SET foodGrant=%s WHERE id=%s',
                     [foodGrant, id])

    # granted non food
    curs.execute('SELECT event.id, \
                         SUM(cost.totalGrant) AS "nonFoodGrant" \
                  FROM   event, cost \
                  WHERE  cost.cType!="Food" \
                         AND  cost.eventID=event.id \
                         AND event.fundingDeadline=%s \
                  GROUP  BY event.id',
                 [fundingDeadline])
    grantedNonFood = curs.fetchall()
    for nonFoodCost in grantedNonFood:
        id = nonFoodCost['event.id']
        nonFoodGrant = nonFoodCost['nonFoodGrant']
        curs.execute('UPDATE event SET nonFoodGrant=%s WHERE id=%s',
                     [nonFoodGrant, id])

    return "All events' granted costs have been updated."

# calculate dollar per student ratio
def calcDollarStud(conn, fundingDeadline):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('UPDATE event \
                  SET    dollarStud=((foodAlloc+nonFoodAlloc)/students) \
                  WHERE  fundingDeadline=%s',
                 [fundingDeadline])
    return "Dollar per student ratios have been successfully calculated for \
           all events."

# recursive allocation helper function
# allocation rules are as follows:
# funding is based on dollar per student
# every event is given a penny for each student it serves
# until the funding deadling budget runs out
# or all events are fully funded
def allocationHelperHead(conn, fundingDeadline):
    message1 = allocationHelperTail(conn, fundingDeadline, "food")
    message2 = allocationHelperTail(conn, fundingDeadline, "non food")
    return message1+" "+message2

def allocationHelperTail(conn, fundingDeadline, kind):
    if kind == "food":
        kindAlloc = "foodAlloc"
        budgetKind = "budgetFood"
        kindGrant = "foodGrant"
        fullyAllocatedKind = "fullyAllocatedFood"
    else:
        kindAlloc = "nonFoodAlloc"
        budgetKind = "budgetNonFood"
        kindGrant = "nonFoodGrant"
        fullyAllocatedKind = "fullyAllocatedNonFood"

    curs = conn.cursor(MySQLdb.cursors.DictCursor)

    # check if there are any funds still available to allocate
    curs.execute('SELECT SUM(%s) as "allocated" \
                  FROM   event \
                  WHERE  fundingDeadline=%s',
                 [kindAlloc, fundingDeadline])
    info = curs.fetchone()
    allocated = info['allocated']
    curs.execute('SELECT * FROM funding WHERE deadline=%s', [fundingDeadline])
    info = curs.fetchone()
    budget = info[budgetKind]
    fundsAvail = (budget>allocated)

    # continue to allocate funds if available
    if fundsAvail:
        # calculate dollar per student budget guaranteed to fully fund given
        # total number of students all events servicing
        curs.execute('SELECT SUM(event.students) AS "totalStudents" \
                      FROM   event \
                      WHERE  %s=FALSE \
                             fundingDeadline=%s',
                     [fullyAllocatedKind, fundingDeadline])
        info = curs.fetchone()
        totalStudents = info['totalStudents']
        avgDollarStud = fundsAvail/totalStudents

        # fund every event up to the guaranteed dollar per student calculated
        # fund event fully if less than dollar per student
        # fullyAllocatedKind True
        curs.execute('UPDATE event \
                      SET    %s=%s \
                             %s=TRUE \
                      WHERE  %s<=%s',
                     [kindAlloc, kindGrant, fullyAllocatedKind, kindGrant,
                     avgDollarStud])
        # fund event guaranteed dollar per student if granted more
        # fullyAllocatedKind False
        curs.execute('UPDATE event \
                      SET    %s=%s \
                      WHERE  %s=FALSE',
                     [kindAlloc, avgDollarStud, fullyAllocatedKind])

        # recurse to make sure all budget fully exhausted
        allocationHelperTail(conn, fundingDeadline, kind)

    # set fullyAllocated (food & non) to True for all events once out of funds
    else:
        curs.execute('UPDATE event \
                      SET    fullyAllocatedFood=TRUE, \
                             fullyAllocatedNonFood=TRUE')

    return "All "+kind+" funds fully exhausted."

# calculate allocated money for all events
def calcAllocated(conn, fundingDeadline):
    if allReviewed(conn, fundingDeadline):
        calcGranted(conn, fundingDeadline)
        curs = conn.cursor(MySQLdb.cursors.DictCursor)

        # automatically cut all events that were granted < 40% requested
        curs.execute('UPDATE event \
                      SET    fullyAllocatedFood=TRUE, \
                             fullyAllocatedNonFood=TRUE, \
                             foodAlloc=0.00, \
                             nonFoodAlloc=0.00 \
                      WHERE  (foodGrant+nonFoodGrant)/(foodReq+nonFoodReq)<0.4')

        message = allocationHelper(conn, fundingDeadline)

        return "All events' budget have been allocated. "+message
    else:
        return "Not all events and appeals have been reviewed."
