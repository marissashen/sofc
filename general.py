#!/usr/local/bin/python2.7

import sys
import MySQLdb
import dbconn2

# ------------------------------------------------------------------------------

# add new user
def addUser(conn, username):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('INSERT INTO user (username) \
                  VALUES           (%s) \
                  ON DUPLICATE KEY UPDATE loginTimes = loginTimes+1',
                 [username])

# return all unreviwed costs for a cost type
# cType must be all lowercase (same case as table name)
def unreviewedCost(conn, fundingDeadline, cType):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT cost.totalReq, \
                         %s.* \
                  FROM   cost, event, %s \
                  WHERE  cost.eventID=event.id \
                         AND cost.id=%s.id \
                         AND event.deadline=%s \
                         AND cost.reviewed=FALSE',
                 [cType, cType, cType, fundingDeadline])
    info = curs.fetchall()
    return info

# return all unreviewed costs & appeals
def allUnreviewed(conn, fundingDeadline):
    # costs
    attendeeCosts = unreviewedCost(conn, fundingDeadline, "attendee")
    foodCosts = unreviewedCost(conn, fundingDeadline, "food")
    formulaCosts = unreviewedCost(conn, fundingDeadline, "formula")
    honorariumCosts = unreviewedCost(conn, fundingDeadline, "honorarium")
    supplyCosts = unreviewedCost(conn, fundingDeadline, "supply")

    # appeals
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT appeal.* \
                  FROM   appeal, cost, event \
                  WHERE  cost.eventID=event.id \
                         AND cost.id=appeal.id \
                         AND event.deadline=%s \
                         AND appeal.reviewed=FALSE',
                 [fundingDeadline])
    appeals = curs.fetchall()

    return (attendeeCosts, foodCosts, formulaCosts, honorariumCosts,
           supplyCosts, appeals)

# return all costs & appeals for an event
def allCostsAppeals(conn, eventID):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * FROM cost WHERE eventID=%s ORDER BY totalReq',
                 [eventID])
    costsOnly = curs.fetchall()
    curs.execute('SELECT cost.*, appeal.* \
                  FROM   cost, appeal \
                  WHERE  cost.eventID=appeal.eventID \
                         AND cost.eventID=%s \
                  ORDER  BY cost.totalReq',
                 [eventID])
    costsWithAppeal = curs.fetchall()
    return (costsOnly, costsWithAppeal)

# return all events for an org ever
def allEventsEver(conn, orgName):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT id, eventName, eventDate, eType, foodReq, nonFoodReq \
                  FROM   event \
                  WHERE  orgName=%s \
                  ORDER BY eventName',
                 [orgName])
    info = curs.fetchall()
    return info

# return all events for an org for a given deadline
def allEventsNow(conn, orgName, fundingDeadline):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT id, eventName, eventDate, eType, foodReq, nonFoodReq \
                  FROM   event \
                  WHERE  orgName=%s \
                         AND fundingDeadline=%s \
                  ORDER BY eventName',
                 [orgName, fundingDeadline])
    info = curs.fetchall()
    return info

# return event info given event id
def eventInfo(conn, eventID):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * FROM event WHERE id=%s',
                 [eventID])
    info = curs.fetchall()
    return info

# return event costs (no appeals)
def eventCosts(conn, eventID):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT cost.* \
                  FROM   cost, appeal \
                  WHERE  cost.eventID=%s \
                         AND pass',
                 [eventID])
    info = curs.fetchall()
    return info

# return event costs (has appeals)
def eventCostsAppeals(conn, eventID):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT cost.* \
                  FROM   cost, appeal \
                  WHERE  cost.eventID=%s \
                         AND cost.id=appeal.id',
                 [eventID])
    info = curs.fetchall()
    return info

# return all orgs that can apply for sofc funds (names & sofc num)
def allSOFCOrgs(conn):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT name, sofc FROM org WHERE canApply=TRUE')
    info = curs.fetchall()
    return info

# return all orgs (names & sofc num)
def allOrgs(conn):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT name, sofc FROM org')
    info = curs.fetchall()
    return info

# return all funding deadlines (dates & type)
def allDeadlines(conn):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT deadline, fType FROM funding')
    info = curs.fetchall()
    return info

# return all info on an org
def orgInfo(conn, sofc):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * FROM org WHERE sofc=%s',
                 [sofc])
    info = curs.fetchone()
    return info
