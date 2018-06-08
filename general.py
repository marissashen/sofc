#!/usr/local/bin/python2.7

import sys
import MySQLdb
import dbconn2
import treasurer, sofc, admin

# ------------------------------------------------------------------------------

# add new user
def addUser(conn, username):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('INSERT INTO user (username) VALUES %s',
                 [username])

# returns all unreviewed costs & appeals
def allUnreviewed(conn, fundingDeadline):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT cost.id, \
                         cost.totalReq \
                         cost.cType \
                  FROM   cost, event \
                  WHERE  cost.eventID=event.ID \
                         AND event.deadline=%s',
                 [fundingDeadline])
