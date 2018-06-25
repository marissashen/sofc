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
def addDeadline(conn, username, deadline, fType, budgetFood, budgetNonFood):
    if isAdmin(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('INSERT INTO funding \
                                  (deadline, fType, budgetFood, budgetNonFood) \
                      VALUES      (%s, %s, %s, %s)',
                     [deadline, fType, budgetFood, budgetNonFood])
        return "Deadline has been successfully added."
    else:
        return "You are not authorized to create a funding deadline."

# add user as a treasurer
def addTreasurer(conn, username, orgName, treasurer):
    if isAdmin(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('INSERT INTO treasurer \
                                  (orgName, username) \
                      VALUES (%s, %s)',
                     [orgName, treasurer])
        return "Treasurer "+treasurer+" for "+orgName+" has been successfully \
               added."
    else:
        return "You are not authorized to add a treasurer."

# delete user as a treasurer
def deleteTreasurer(conn, username, orgName, treasurer):
    if isAdmin(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('DELETE FROM treasurer \
                      WHERE       orgName=%s, \
                                  username=%s',
                     [orgName, treasurer])
        return "Treasurer "+treasurer+" for "+orgName+" has been successfully \
               deleted."
    else:
        return "You are not authorized to delete a treasurer."

# add user as a SOFC member
def addSOFC(conn, username, SOFC):
    if isAdmin(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('INSERT INTO user \
                                  (username, uType) \
                      VALUES      (%s, %s) \
                      ON DUPLICATE KEY UPDATE uType=%s',
                     [SOFC, 'sofc', 'sofc'])
        return "SOFC member "+SOFC+" has been successfully added."
    else:
        return "You are not authorized to add a SOFC member."

# delete user as a SOFC member
def deleteSOFC(conn, username, SOFC):
    if isAdmin(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('UPDATE user \
                      SET    uType=1 \
                      WHERE  username=%s',
                     [SOFC])
        return "SOFC member "+SOFC+" has been successfully deleted."
    else:
        return "You are not authorized to delete a SOFC member."

# add new org
def addOrg(conn, username name, classification, sofc, profit):
    if isAdmin(conn, username):
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
    else:
        return "You are not authorized to add an org."

# delete org
def deleteOrg(conn, username, name):
    if isAdmin(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('DELETE FROM org WHERE name=%s', [name])
        return "Org "+name+" has been successfully deleted."
    else:
        return "You are not authorized to delete an org."

# update org
def updateOrg(conn, username, oldName, newName, classification, sofc, profit):
    if isAdmin(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('UPDATE org \
                      SET    name=%s, \
                             classification=%s, \
                             sofc=%s \
                             profit=%s \
                      WHERE  name=%s',
                     [newName, classification, sofc, profit, oldName])
        return "Org "+newName+" has been successfully updated."
    else:
        return "You are not authorized to update org information."

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
