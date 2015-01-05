#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# written by Benedikt Waldvogel

from flask import Flask, render_template, flash, redirect, request, url_for
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from model import db, LogEntry, User, Sample
import json
from datetime import timedelta, date, datetime
import math
import time
import os
from flask_wtf import Form
from wtforms import TextField, PasswordField
from flask_bcrypt import Bcrypt
import old_xml_import
import sml_import
import gpx_export
import dateutil.parser
import gzip
from flask.helpers import make_response

app = Flask('openmoves')

login_manager = LoginManager()
app_bcrypt = Bcrypt()


class LoginForm(Form):
    username = TextField()
    password = PasswordField()


def formatTime(time):
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def isoDate(date):
    return date.strftime("%Y-%m-%dT%H:%M:%S.%f%z")


def fromIsoDate(dateString):
    return datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S.%f%z")


def duration(value):
    if isinstance(value, str):
        value = timedelta(seconds=float(value))
    elif isinstance(value, float) or isinstance(value, int):
        value = timedelta(seconds=float(value))

    hours, remainder = divmod(value.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return '%02d:%02d:%05.2f' % (hours, minutes, seconds)


def radianToDegree(value):
    return 180.0 / math.pi * value


def unixEpoch(date):
    return 1000 * time.mktime(date.timetuple())


def jsonify(value):
    if value:
        return json.dumps(value)


app.jinja_env.filters['jsonify'] = jsonify
app.jinja_env.filters['formatTime'] = formatTime
app.jinja_env.filters['isoDate'] = isoDate
app.jinja_env.filters['duration'] = duration
app.jinja_env.filters['degree'] = radianToDegree
app.jinja_env.filters['epoch'] = unixEpoch


def init(configFile='openmoves.cfg'):
    app.config.from_pyfile('openmoves.cfg.default', silent=False)
    if configFile:
        app.config.from_pyfile(configFile, silent=True)

    if "SECRET_KEY" not in app.config or not app.config["SECRET_KEY"]:
        print("WARNING: no secret key configured. Using a random secret key")
        print("Please run 'initialize_config.py' or set SECRET_KEY in '%s'" % configFile)
        app.config["SECRET_KEY"] = os.urandom(32)

    db.init_app(app)

    Bootstrap(app)
    app_bcrypt.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "login"
    return app


@login_manager.user_loader
def load_user(username):
    return User.query.filter_by(username=username).scalar()


@app.route('/import', methods=['GET', 'POST'])
@login_required
def moveImport():
    xmlfiles = request.files.getlist('files')
    importedMoves = []

    for xmlfile in xmlfiles:
        move = None
        filename = xmlfile.filename
        if filename.endswith('.gz'):
            xmlfile = gzip.GzipFile(fileobj=xmlfile, mode='rb', filename=filename)
            filename = filename[:-len('.gz')]

        if filename.endswith('.xml'):
            move = old_xml_import.oldXmlImport(xmlfile)
        elif filename.endswith('.sml'):
            move = sml_import.smlImport(xmlfile)
        else:
            flash("unknown fileformat: '%s'" % xmlfile.filename, 'error')

        if move:
            importedMoves.append(move)

    if importedMoves:
        if len(importedMoves) == 1:
            move = importedMoves[0]
            flash("imported '%s': move %d" % (xmlfile.filename, move.id))
            return redirect(url_for('move', id=move.id))
        else:
            flash("imported %d moves" % len(importedMoves))
            return redirect(url_for('moves'))
    else:
        return render_template('import.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = load_user(username=form.username.data)
        if not user:
            flash("no such user", 'error')
            return render_template('login.html', form=form)

        if app_bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)

            return redirect(request.args.get('next') or url_for('moves'))
        else:
            flash("login failed", 'error')
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/")
def index():
    nrOfMoves = LogEntry.query.count()

    return render_template('index.html', nrOfMoves=nrOfMoves)


@app.route("/dashboard")
@login_required
def dashboard():
    now = datetime.utcnow()
    # Determine dashboad startDate
    if 'startDate' in request.args:
        startDate = dateutil.parser.parse(request.args.get('startDate'))
    else:
        startDate = date(now.year, now.month, now.day) - timedelta(days=7)
    # Determine dashboad endDate
    if 'endDate' in request.args:
        endDate = dateutil.parser.parse(request.args.get('startDate'))
    else:
        endDate = date(now.year, now.month, now.day)

    moves = LogEntry.query.filter_by(user=current_user).filter(LogEntry.dateTime >= startDate).filter(LogEntry.dateTime <= endDate).order_by(LogEntry.dateTime.asc()).all()

    totalDistance = 0
    totalDuration = timedelta(0)
    totalAscent = 0
    totalDescent = 0
    for move in moves:
        totalDistance += move.distance
        totalDuration += move.duration
        if move.ascent:
            totalAscent += move.ascent
        if move.descent:
            totalDescent += move.descent

    nrOfMoves = len(moves)

    return render_template('dashboard.html', moves=moves,
                           startDate=startDate, endDate=endDate,
                           nrOfMoves=nrOfMoves,
                           totalDistance=totalDistance, totalDuration=totalDuration,
                           totalAscent=totalAscent, totalDescent=totalDescent)


@app.route("/moves")
@login_required
def moves():
    moves = moves = LogEntry.query.filter_by(user=current_user)
    totalMovesCount = moves.count()
    sort = request.args.get('sort')
    sortOrder = request.args.get('sortOrder')
    sortDefault = 'dateTime'
    if not sort:
        sort = sortDefault
        sortOrder = 'desc'
    if not sortOrder:
        sortOrder = 'asc'

    if not hasattr(LogEntry, sort):
        flash("illegal sort field: %s" % sort, 'error')
        sort = sortDefault

    sortAttr = getattr(LogEntry, sort)
    if not sortOrder or sortOrder == 'asc':
        sortAttr = sortAttr.asc()
    else:
        sortAttr = sortAttr.desc()

    if db.engine.name == "postgresql":
        sortAttr = sortAttr.nullslast()

    moves = moves.order_by(sortAttr)
    return render_template('moves.html', moves=moves, totalMovesCount=totalMovesCount, sort=sort, sortOrder=sortOrder)


@app.route("/moves/<int:id>/delete")
@login_required
def deleteMove(id):
    move = LogEntry.query.filter_by(user=current_user, id=id).scalar()
    if not move:
        flash("move %d not found" % id, 'error')
    else:
        Sample.query.filter_by(logEntry=move).delete(synchronize_session=False)
        db.session.delete(move)
        db.session.commit()
        flash("move %d deleted" % id, 'success')

    return redirect(url_for('moves'))


@app.route("/moves/<int:id>/export")
@login_required
def exportMove(id):
    move = LogEntry.query.filter_by(user=current_user, id=id).scalar()
    if not move:
        flash("move %d not found" % id, 'error')
    else:
        if "format" in request.args:
            format = request.args.get("format").lower()
        else:
            format = "gpx"  # default

        formatHandlers = {}
        formatHandlers['gpx'] = gpx_export.gpxExport
        # formatHandlers['tcx'] = exportTcx
        if format in formatHandlers:
            exportFile = formatHandlers[format](move)
            if not exportFile:
                return redirect(url_for('move', id=id))
            response = make_response(exportFile)
            response.headers["Content-Disposition"] = "attachment; filename= %s_%s_%s.%s" % (isoDate(move.dateTime), move.activity, move.id, format)
            return response
        else:
            flash("Export format %s not supported" % format, 'error')

    return redirect(url_for('move', id=id))


@app.route("/moves/<int:id>")
@login_required
def move(id):
    move = LogEntry.query.filter_by(user=current_user, id=id).scalar()
    if not move:
        flash("move %s not found" % id, 'error')
        return redirect(url_for('moves'))

    samples = move.samples.order_by('time asc').all()
    events = [sample for sample in samples if sample.events]

    filteredEvents = []
    pauses = []
    laps = []
    pauseBegin = None
    for sample in events:
        assert len(sample.events.keys()) == 1
        if 'pause' in sample.events:
            state = sample.events['pause']['state'].lower() == 'true'
            if state:
                pauseBegin = sample
            elif not state and pauseBegin:
                pauses.append([pauseBegin, sample])
        elif 'lap' in sample.events:
            laps.append(sample)
        else:
            filteredEvents.append(sample)

    gpsSamples = [sample for sample in samples if sample.sampleType and sample.sampleType.startswith('gps-')]

    # gpsSamples = [sample for sample in gpsSamples if not sample.ehpe or sample.ehpe < 30]

    activity = "".join([a[0].upper() + a[1:] for a in move.activity.split(" ")])
    activity = activity[0].lower() + activity[1:]
    return render_template("move/%s.html" % activity, move=move, samples=samples, events=filteredEvents, pauses=pauses, laps=laps, gpsSamples=gpsSamples)

if __name__ == '__main__':
    init().run()
