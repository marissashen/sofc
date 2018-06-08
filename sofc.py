#!/usr/local/bin/python2.7

import sys
import MySQLdb
import dbconn2
import general, treasurer, admin

# ------------------------------------------------------------------------------

# check if user is sofc or admin (can comment & approve events)
def isSOFC(conn, username):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT uType FROM user WHERE username=%s', [username])
    info = curs.fetchone()
    return info['uType'] == "sofc" or info['uType'] == "admin"

# review cost
def reviewCost(conn, username, id):
    if isSOFC(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('UPDATE cost \
                      SET    reviewer=%s, \
                             reviewed=TRUE \
                      WHERE  id=%s',
                     [username, id])
        return "Cost has been successfully reviewed."

    else:
        return "You are not listed as a SOFC member. Please contact \
                bursarsoffice@wellesley.edu if this is a mistake."

# grant money to cost (can be different from total requested)
# updates grant money if already granted some earlier
def grantMoney(conn, username, id, totalGrant):
    if isSOFC(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('SELECT * FROM cost WHERE id=%s', [id])
        info = curs.fetchone()
        eventID = info['eventID']
        reviewed = info['reviewed']
        oldGranted = info['totalGrant']
        cType = info['cType']

        message = reviewCost(conn, username, id)
        curs.execute('UPDATE cost SET totalGrant=%s WHERE id=%s',
                     [totalGrant, id])

        # get diff of old granted amount & new to update event total granted
        diff = totalGrant-oldGranted
        if cType == "Food":
            curs.execute('UPDATE event \
                          SET    foodGrant=foodGrant+%s \
                          WHERE  eventID=%s',
                         [diff, eventID])
        else:
            curs.execute('UPDATE event \
                          SET    nonFoodGrant=nonFoodGrant+%s\
                          WHERE  eventID=%s',
                         [diff, eventID])
        return message+" Money successfully granted/updated."
    else:
        return "You are not listed as a SOFC member. Please contact \
                bursarsoffice@wellesley.edu if this is a mistake."

# return commentor and comment on cost (is None, None if no comment made)
def returnComment(conn, id):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * FROM comment WHERE id=%s', [id])
    info = curs.fetchone()
    commentor = info['commentor']
    note = info['note']
    return commentor, note

# add comment on cost
def addComment(conn, username, id, note):
    if isSOFC(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        reviewCost(conn, username, id)
        curs.execute('INSERT INTO comment \
                                  (id, commentor, note) \
                      VALUES      (%s, %s, %s)',
                     [id, username, note])
        return "Comment successfully added."
    else:
        return "You are not listed as a SOFC member. Please contact \
                bursarsoffice@wellesley.edu if this is a mistake."

# delete comment
def deleteComment(conn, username, id):
    if isSOFC(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('DELETE FROM comment WHERE id=%s', [id])
        return "Comment successfully deleted."
    else:
        return "You are not listed as a SOFC member. Please contact \
                bursarsoffice@wellesley.edu if this is a mistake."

# update comment
def updateComment(conn, username, id, note):
    if isSOFC(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('UPDATE comment \
                      SET    commentor=%s, \
                             note=%s \
                      WHERE  id=%s',
                     [username, note, id])
        return "Comment successfully updated."
    else:
        return "You are not listed as a SOFC member. Please contact \
                bursarsoffice@wellesley.edu if this is a mistake."

# check if appeal exists for cost already
def hasAppeal(conn, id):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('SELECT * FROM appeal WHERE id=%s', [id])
    info = curs.fetchone()
    return info is not None

# request appeal (also leaves a comment for what to put in appeal)
def reqAppeal(conn, username, id, note):
    if isSOFC(conn, username):
        addComment(conn, username, id, note)
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('INSERT INTO appeal (id, requestor) VALUES (%s, %s, %s)',
                     [id, username])
        return "Appeal successfully requested."
    else:
        return "You are not listed as a SOFC member. Please contact \
                bursarsoffice@wellesley.edu if this is a mistake."

# rescind appeal request (only deletes if treasurer has not been added yet)
# deleteComment is boolean on whether comment for cost needs to be deleted
def resAppeal(conn, username, id, deleteComment):
    if isSOFC(conn, username):
        if deleteComment:
            deleteComment(conn, username, id)

        # check if treasurer is in the appeal
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('SELECT * FROM appeal WHERE id=%s', [id])
        info = curs.fetchone()
        treasurer = info['treasurer']

        if treasurer:
            return "Treasurer has already been added to the appeal. Appeal \
                   cannot be rescinded."
        else:
            curs.execute('DELETE FROM appeal WHERE id=%s', [id])
            return "Appeal request successfully rescinded."
    else:
        return "You are not listed as a SOFC member. Please contact \
                bursarsoffice@wellesley.edu if this is a mistake."

# pass appeal
def passAppeal(conn, username, id, totalGrant):
    if isSOFC(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('UPDATE appeal \
                      SET    reviewed=TRUE, \
                             passer=%s, \
                             passed=TRUE \
                      WHERE  id=%s',
                     [username, id])
        message = grantMoney(conn, username, id, totalGrant)
        return "Appeal successfully passed. "+message
    else:
        return "You are not listed as a SOFC member. Please contact \
                bursarsoffice@wellesley.edu if this is a mistake."

# cut appeal
def cutAppeal(conn, username, id, totalGrant):
    if isSOFC(conn, username):
        curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('UPDATE appeal \
                      SET    reviewed=TRUE, \
                             passer=%s, \
                             passed=FALSE \
                      WHERE  id=%s',
                     [username, id])
        message = grantMoney(conn, username, id, totalGrant)
        return "Appeal successfully cut. "+message
    else:
        return "You are not listed as a SOFC member. Please contact \
                bursarsoffice@wellesley.edu if this is a mistake."
