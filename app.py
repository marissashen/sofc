from flask import (Flask, render_template, make_response, url_for, request, redirect, flash, session, send_from_directory, jsonify)
from werkzeug import secure_filename
from flask_cas import CAS

import os
import imghdr

app = Flask(__name__)
CAS(app)

import sys, random, dbconn2, datetime
import general, treasurer, sofc, admin

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
    else:
        return redirect(url_for('login'))

    general.addUser(conn, username)
    return render_template('home.html',
                               uName = username,
                               opportunities=getOpps(conn),
                               picture_exists=exists,
                               src=src)

@app.route('/home/', methods=['POST'])
def home():
    conn = dbconn2.connect(DSN)

    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
    else:
        return redirect(url_for('login'))

    # add new job
    if request.form['submit'] == "Add New Job":
        return redirect(url_for('addNewJob'))

    # filter through all opportunities
    if request.form['submit'] == "Filter":
        # try & except (do not need to check something for all filters)
        try:
            classPref = request.form['classPref']
        except:
            classPref = False
        try:
            jobType = request.form['jobType']
        except:
            jobType = False
        try:
            jobTitle = request.form['jobTitle']
        except:
            jobTitle = False
        try:
            season = request.form['season']
        except:
            season = False

        jobs = search.searchJobs(conn, classPref, jobTitle, jobType, season)
        return render_template('home.html',
                               uName=username,
                               opportunities=jobs,
                               src=src,
                               picture_exists=exists)

@app.route('/addNewJob/', methods=['GET','POST'])
def addNewJob():

    conn = dbconn2.connect(DSN)

    if 'bnum' in session:
        bnum = session['bnum']
    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
    else:
        flash('Please login to view this page content')
        return redirect(url_for('login'))

    src,exists = getSrc(conn, bnum)

    formErr = 'Please fill in the blank fields'

    if request.method == 'GET':
        return render_template('job_form.html',
                               uName=username,
                               companies=opp.allCompany(conn),
                               picture_exists=exists,
                               src=src)

    if request.method == 'POST':
        if request.form['submit'] == 'submit':
            link = request.form['link']
            classPref = request.form['classPref'] #radio button
            jobTitle = request.form['jobTitle'] #radio button
            jobType = request.form['jobType'] #radio button
            positionName = request.form['positionName']
            season = request.form['season'] #radio button
            deadline = request.form['deadline']
            company = request.form['companyName'] #can only add in one job
            city = request.form['location']
            if company == 'none':
                company = request.form['newCompany']
            jobID = opp.addJob(conn, bnum, company, link, classPref, jobType, jobTitle, positionName, season, deadline)
            opp.addJobLoc(conn, bnum, jobID, city)
            flash(city+' added for job')
            return redirect(url_for('addJobLocation', jobID=jobID))

@app.route('/addJobLocation/<jobID>', methods=['GET','POST'])
def addJobLocation(jobID):

    conn = dbconn2.connect(DSN)

    if 'bnum' in session:
        bnum = session['bnum']
    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
    else:
        flash('Please login to view this page content.')
        return redirect(url_for('login'))

    src,exists = getSrc(conn, bnum)

    if request.method == 'GET':
        cities = opp.allCities(conn)
        return render_template('jobLocation.html',
                               jobID=jobID,
                               cities=cities,
                               uName=username,
                               src=src,
                               picture_exists=exists)

    if request.method == 'POST':
        if request.form['submit'] == 'submit':
            cities = opp.allCities(conn)
            if cities:
                try:
                    locations = request.form.getlist('city')
                    for city in locations:
                        flash(city+' added for job.')
                        opp.addJobLoc(conn, bnum, jobID, city)
                except:
                    pass
            newLocation = request.form[('newLocation')]
            if newLocation: #can a user submit with an empty value
                opp.addCity(conn, newLocation)
                opp.addJobLoc(conn, bnum, jobID, newLocation)
                flash('New city '+newLocation+' added for job.')
        return redirect(url_for('home'))

@app.route('/job/<jobID>', methods=['GET', 'POST'])
def job(jobID):
    conn = dbconn2.connect(DSN)

    if 'bnum' in session:
        bnum = session['bnum']
    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
    else:
        flash('Please login to view this page content.')
        return redirect(url_for('login'))

    src,exists = getSrc(conn, bnum)

    # displays job info & reviews

    #checks if a job is saved
    if checkSaved(conn,jobID) is None:
        saved = False;
    else:
        saved = True;

    if request.method == 'GET':
        (job, locations, reviews) = search.findJob(conn, jobID, bnum)
        return render_template('job.html',
                               bnum=bnum,
                               uName=username,
                               job=job,
                               locations=locations,
                               reviews=reviews,
                               src=src,
                               picture_exists=exists,
                               saved = saved)

    if request.method == 'POST':
        # if user wants to add a review for job --> redirects to review form
        if request.form['submit'] == 'Add Job Review':
            return redirect(url_for('addNewReview',
                                    jobID=jobID))

        # if user wants to edit their own review --> redirects to update form
        if request.form['submit'] == 'Edit Review':
            return redirect(url_for('editReview',
                                    jobID=jobID))

        # if user wants to delete their own review --> rerenders page
        if request.form['submit'] == 'Delete Review':
            deleteJobRev(conn, bnum, jobID)
            (job, locations, reviews) = search.findJob(conn, jobID, bnum)
            return render_template('job.html',
                                   bnum=bnum,
                                   uName=username,
                                   job=job,
                                   locations=locations,
                                   reviews=reviews,
                                   src=src,
                                   picture_exists=exists,
                                   saved = saved)
        #user saves a job --> create a table entry with the saved job and bnum
        if request.form['submit'] == 'Save':
            saveJob(conn,jobID,bnum)
            (job, locations, reviews) = search.findJob(conn, jobID, bnum)
            return render_template('job.html',
                                   bnum=bnum,
                                   uName=username,
                                   job=job,
                                   locations=locations,
                                   reviews=reviews,
                                   src=src,
                                   picture_exists=exists,
                                   saved = True)

        #user unsaves a job --> remove that entry from the saves table
        if request.form['submit'] == 'Unsave':
            deleteSavedJob(conn,jobID,bnum)
            (job, locations, reviews) = search.findJob(conn, jobID, bnum)
            return render_template('job.html',
                                   bnum=bnum,
                                   uName=username,
                                   job=job,
                                   locations=locations,
                                   reviews=reviews,
                                   src=src,
                                   picture_exists=exists,
                                   saved = False)




@app.route('/addNewReview/<jobID>', methods=['GET','POST'])
def addNewReview(jobID):

    conn = dbconn2.connect(DSN)
    job = getJobName(conn,jobID)
    jobName = job['positionName']
    if 'bnum' in session:
        bnum = session['bnum']
    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
    else:
        flash('Please login to view this page content.')
        return redirect(url_for('login'))

    src,exists = getSrc(conn, bnum)

    if request.method == 'GET':
        return render_template('review_form.html',
                               jobName=jobName,
                               uName=username,
                               src=src,
                               picture_exists=exists)

    if request.method == 'POST':
        if request.form['submit'] == 'Submit Review':
            jobYear = request.form[('jobYear')]
            review = request.form[('review')]

            addJob = addJobRev(conn, bnum, jobID, jobYear, review)
            if not addJob:
                flash("A review already exists for this job and user.")
            else:
                flash("Review added successfully.")
            return redirect(url_for('job', jobID=jobID))

# editting a review user made
@app.route('/editReview/<jobID>', methods=['GET','POST'])
def editReview(jobID):

    conn = dbconn2.connect(DSN)
    job = getJobName(conn,jobID)
    jobName = job['positionName']

    if 'bnum' in session:
        bnum = session['bnum']
    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
    else:
        flash('Please login to view this page content.')
        return redirect(url_for('login'))

    src,exists = getSrc(conn, bnum)

    if request.method == 'GET':
        rev = getRev(conn, bnum, jobID)
        if rev is None:
            flash('You do not have a review for this job.')
            return redirect(url_for('job', jobName=jobName))
        return render_template('update_review.html',
                               uName=username,
                               jobName=jobName,
                               jobYear=rev['jobYear'],
                               review=rev['review'],
                               src=src,
                               picture_exists=exists)

    if request.method == 'POST':
        if request.form['submit'] == 'Update Review':
            jobYear = request.form[('jobYear')]
            review = request.form[('review')]

            update = updateJobRev(conn, bnum, jobID, jobYear, review)
            return redirect(url_for('job',jobID = jobID, jobName=jobName))


@app.route('/profile/', methods=["GET", "POST"])
def profile():

    conn = dbconn2.connect(DSN)

    if 'bnum' in session:
        bnum = session['bnum']
        user = getUserInfo(conn, bnum)
        username = user['username']

        src,exists = getSrc(conn, bnum)

    #loading in saves
    savedJobs = list()
    jobs = getSavedJobs(conn,bnum)

    if jobs is not None:
        for job in jobs:
            savedJobs.append(getJobInfo(conn,job['jobID']))
    else:
        savedJobs = None

    if request.method == 'GET':
        return render_template('profile.html',
                               user=user,
                               uName=username,
                               src=src,
                               picture_exists=exists,
                               saved = savedJobs)
    else: #upload
        if request.form['submit'] == 'Update Picture':
            try:
                f = request.files['photo']
                mime_type = imghdr.what(f.stream)
                if mime_type != 'jpeg': # only allows JPEGs to be uploaded
                    raise Exception('Not a JPEG')
                filename = secure_filename(str(bnum)+'.jpeg')
                pathname = 'images/'+filename
                f.save(pathname)
                flash('Upload successful.')
                addProfPic(conn, bnum, pathname)
                return render_template('profile.html',
                                   bnum=bnum,
                                   user=user,
                                   uName=username,
                                   src=src,
                                   picture_exists=exists,
                                   saved = savedJobs)

            except Exception as err:
                flash('Upload failed: {why}'.format(why=err)+".")
                return render_template('profile.html',
                                   bnum=bnum,
                                   user=user,
                                   uName=username,
                                   src=src,
                                   picture_exists=exists,
                                   saved = savedJobs)

        if request.form['submit'] == 'Delete Picture':
            deleteProfPic(conn, bnum)
            return render_template('profile.html',
                                   bnum=bnum,
                                   user=user,
                                   uName=username,
                                   src=src,
                                   saved = savedJobs)

#uploading pic route
@app.route('/pic/<fname>')
def pic(fname):
    f = secure_filename(fname)
    return send_from_directory('images',f)


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
