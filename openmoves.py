#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# written by Benedikt Waldvogel

from flask import Flask, render_template, flash, redirect, request, url_for
from flask_bootstrap import Bootstrap
from flask_login import login_user, current_user, login_required, logout_user
from model import db, Move, Sample
from datetime import timedelta, date, datetime
from sqlalchemy.sql import func
import os
from flask_bcrypt import Bcrypt
import old_xml_import
import sml_import
import gpx_export
import dateutil.parser
import gzip
from flask.helpers import make_response
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand
from commands import AddUser
from filters import register_filters
from login import login_manager, load_user, LoginForm

app = Flask('openmoves')

app_bcrypt = Bcrypt()
migrate = Migrate(app, db)

register_filters(app)


def initialize_config(f):

    random_bytes = os.urandom(32)

    if isinstance(random_bytes[0], str):
        random_bytes = [ord(c) for c in random_bytes]

    data = "SECRET_KEY = '%s'\n" % "".join("{:02x}".format(c) for c in random_bytes)
    f.write(data)


def init(configFile):
    app.config.from_pyfile('openmoves.cfg.default', silent=False)
    if configFile:
        if not os.path.exists(configFile):
            with open(configFile, 'w') as f:
                initialize_config(f)
            print("created %s" % configFile)

        app.config.from_pyfile(configFile, silent=False)
        assert app.config["SECRET_KEY"]

    db.init_app(app)

    with app.app_context():
        if db.engine.name == 'sqlite':
            db.create_all()

    Bootstrap(app)
    app_bcrypt.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "login"

    return app


def command_app_context():
    app.config.update(SQLALCHEMY_ECHO=False)
    return app.app_context()


manager = Manager(init)

manager.add_option('-c', '--config', dest='configFile', default='openmoves.cfg', required=False)

manager.add_command("runserver", Server(use_debugger=True))
manager.add_command('db', MigrateCommand)
manager.add_command('add-user', AddUser(command_app_context, app_bcrypt))


@app.errorhandler(404)
def error404(error):
    return render_template('_404.html'), 404


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
            move.temperatureAvg = db.session.query(func.avg(Sample.temperature)).filter(Sample.move == move, Sample.temperature > 0).one()
            db.session.commit()
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
    nrOfMoves = Move.query.count()

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

    moves = Move.query.filter_by(user=current_user).filter(Move.dateTime >= startDate).filter(Move.dateTime <= endDate).order_by(Move.dateTime.asc()).all()

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
    moves = moves = Move.query.filter_by(user=current_user)
    totalMovesCount = moves.count()
    sort = request.args.get('sort')
    sortOrder = request.args.get('sortOrder')
    sortDefault = 'dateTime'
    if not sort:
        sort = sortDefault
        sortOrder = 'desc'
    if not sortOrder:
        sortOrder = 'asc'

    if not hasattr(Move, sort):
        flash("illegal sort field: %s" % sort, 'error')
        sort = sortDefault

    sortAttr = getattr(Move, sort)
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
    move = Move.query.filter_by(user=current_user, id=id).first_or_404()
    Sample.query.filter_by(move=move).delete(synchronize_session=False)
    db.session.delete(move)
    db.session.commit()
    flash("move %d deleted" % id, 'success')

    return redirect(url_for('moves'))


@app.route("/moves/<int:id>/export")
@login_required
def exportMove(id):
    move = Move.query.filter_by(user=current_user, id=id).first_or_404()

    if "format" in request.args:
        format = request.args.get("format").lower()
    else:
        format = "gpx"  # default

    formatHandlers = {}
    formatHandlers['gpx'] = gpx_export.gpxExport
    # formatHandlers['tcx'] = exportTcx
    if format not in formatHandlers:
        flash("Export format %s not supported" % format, 'error')
        return redirect(url_for('move', id=id))

    exportFile = formatHandlers[format](move)
    if not exportFile:
        return redirect(url_for('move', id=id))
    response = make_response(exportFile)
    dateTime = move.dateTime.strftime("%Y-%m-%dT%H:%M:%S")
    response.headers["Content-Disposition"] = "attachment; filename= %s_%s_%s.%s" % (dateTime, move.activity, move.id, format)
    return response


@app.route("/moves/<int:id>")
@login_required
def move(id):
    move = Move.query.filter_by(user=current_user, id=id).first_or_404()

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

    model = {}
    model['move'] = move
    model['samples'] = samples
    model['events'] = filteredEvents
    model['pauses'] = pauses
    model['laps'] = laps
    model['gpsSamples'] = [sample for sample in samples if sample.sampleType and sample.sampleType.startswith('gps-')]
    if 'swimming' in move.activity:
        model['swimmingEvents'] = [sample for sample in filteredEvents if 'swimming' in sample.events]
        model['swimmingStyleChanges'] = [sample for sample in model['swimmingEvents'] if sample.events['swimming']['type'] == 'StyleChange']
        model['swimmingTurns'] = [sample for sample in model['swimmingEvents'] if sample.events['swimming']['type'] == 'Turn']
        model['swimmingStrokes'] = [sample for sample in model['swimmingEvents'] if sample.events['swimming']['type'] == 'Stroke']
        model['swimPace'] = timedelta(seconds=move.duration.total_seconds() / move.distance)

    # eg. 'Pool swimming' → 'poolSwimming'
    activityName = "".join([a[0].upper() + a[1:] for a in move.activity.split(" ")])
    activityName = activityName[0].lower() + activityName[1:]
    return render_template("move/%s.html" % activityName, **model)

if __name__ == '__main__':
    manager.run()
