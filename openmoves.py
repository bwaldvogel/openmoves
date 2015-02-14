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
import itertools

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


def init(configfile):
    app.config.from_pyfile('openmoves.cfg.default', silent=False)
    if configfile:
        if not os.path.exists(configfile):
            with open(configfile, 'w') as f:
                initialize_config(f)
            print("created %s" % configfile)

        app.config.from_pyfile(configfile, silent=False)
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

manager.add_option('-c', '--config', dest='configfile', default='openmoves.cfg', required=False)

manager.add_command("runserver", Server(use_debugger=True))
manager.add_command('db', MigrateCommand)
manager.add_command('add-user', AddUser(command_app_context, app_bcrypt))


@app.errorhandler(404)
def error404(error):
    return render_template('_404.html'), 404


@app.route('/import', methods=['GET', 'POST'])
@login_required
def move_import():
    xmlfiles = request.files.getlist('files')
    imported_moves = []

    for xmlfile in xmlfiles:
        move = None
        filename = xmlfile.filename
        app.logger.info("importing '%s'" % filename)
        if filename.endswith('.gz'):
            xmlfile = gzip.GzipFile(fileobj=xmlfile, mode='rb', filename=filename)
            filename = filename[:-len('.gz')]

        if filename.endswith('.xml'):
            move = old_xml_import.old_xml_import(xmlfile)
        elif filename.endswith('.sml'):
            move = sml_import.sml_import(xmlfile)
        else:
            flash("unknown fileformat: '%s'" % xmlfile.filename, 'error')

        if move:
            move.temperature_avg, = db.session.query(func.avg(Sample.temperature)).filter(Sample.move == move, Sample.temperature > 0).one()

            stroke_count = 0
            for events, in db.session.query(Sample.events).filter(Sample.move == move, Sample.events != None):
                if 'swimming' in events and events['swimming']['type'] == 'Stroke':
                    stroke_count += 1

            if 'swimming' in move.activity:
                assert stroke_count > 0

            if stroke_count > 0:
                move.stroke_count = stroke_count

            db.session.commit()
            imported_moves.append(move)

    if imported_moves:
        if len(imported_moves) == 1:
            move = imported_moves[0]
            flash("imported '%s': move %d" % (xmlfile.filename, move.id))
            return redirect(url_for('move', id=move.id))
        else:
            flash("imported %d moves" % len(imported_moves))
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
    nr_of_moves = Move.query.count()

    return render_template('index.html', nr_of_moves=nr_of_moves)


@app.route("/dashboard")
@login_required
def dashboard():
    now = datetime.utcnow()
    # Determine dashboad start_date
    if 'start_date' in request.args:
        start_date = dateutil.parser.parse(request.args.get('start_date'))
    else:
        start_date = date(now.year, now.month, now.day) - timedelta(days=7)
    # Determine dashboad end_date
    if 'end_date' in request.args:
        end_date = dateutil.parser.parse(request.args.get('end_date'))
    else:
        end_date = date(now.year, now.month, now.day)

    moves = Move.query.filter_by(user=current_user).filter(Move.date_time >= start_date).filter(Move.date_time <= end_date).order_by(Move.date_time.asc()).all()

    total_distance = 0
    total_duration = timedelta(0)
    total_ascent = 0
    total_descent = 0
    for move in moves:
        total_distance += move.distance
        total_duration += move.duration
        if move.ascent:
            total_ascent += move.ascent
        if move.descent:
            total_descent += move.descent

    nr_of_moves = len(moves)

    return render_template('dashboard.html', moves=moves,
                           start_date=start_date, end_date=end_date,
                           nr_of_moves=nr_of_moves,
                           total_distance=total_distance, total_duration=total_duration,
                           total_ascent=total_ascent, total_descent=total_descent)


@app.route("/moves")
@login_required
def moves():
    moves = moves = Move.query.filter_by(user=current_user)
    total_moves_count = moves.count()
    sort = request.args.get('sort')
    sort_order = request.args.get('sort_order')
    sort_default = 'date_time'
    if not sort:
        sort = sort_default
        sort_order = 'desc'
    if not sort_order:
        sort_order = 'asc'

    if not hasattr(Move, sort):
        flash("illegal sort field: %s" % sort, 'error')
        sort = sort_default

    sort_attr = getattr(Move, sort)
    if not sort_order or sort_order == 'asc':
        sort_attr = sort_attr.asc()
    else:
        sort_attr = sort_attr.desc()

    if db.engine.name == "postgresql":
        sort_attr = sort_attr.nullslast()

    moves = moves.order_by(sort_attr)
    return render_template('moves.html', moves=moves, total_moves_count=total_moves_count, sort=sort, sort_order=sort_order)


@app.route("/moves/<int:id>/delete")
@login_required
def delete_move(id):
    move = Move.query.filter_by(user=current_user, id=id).first_or_404()
    Sample.query.filter_by(move=move).delete(synchronize_session=False)
    db.session.delete(move)
    db.session.commit()
    flash("move %d deleted" % id, 'success')

    return redirect(url_for('moves'))


@app.route("/moves/<int:id>/export")
@login_required
def export_move(id):
    move = Move.query.filter_by(user=current_user, id=id).first_or_404()

    if "format" in request.args:
        format = request.args.get("format").lower()
    else:
        format = "gpx"  # default

    format_handlers = {}
    format_handlers['gpx'] = gpx_export.gpx_export
    if format not in format_handlers:
        flash("Export format %s not supported" % format, 'error')
        return redirect(url_for('move', id=id))

    export_file = format_handlers[format](move)
    if not export_file:
        return redirect(url_for('move', id=id))
    response = make_response(export_file)
    date_time = move.date_time.strftime("%Y-%m-%dT%H:%M:%S")
    response.headers["Content-Disposition"] = "attachment; filename= %s_%s_%s.%s" % (date_time, move.activity, move.id, format)
    return response


@app.route("/moves/<int:id>")
@login_required
def move(id):
    move = Move.query.filter_by(user=current_user, id=id).first_or_404()

    samples = move.samples.order_by('time asc').all()
    events = [sample for sample in samples if sample.events]

    filtered_events = []
    pauses = []
    laps = []
    pause_begin = None
    for sample in events:
        assert len(sample.events.keys()) == 1
        if 'pause' in sample.events:
            state = sample.events['pause']['state'].lower() == 'true'
            if state:
                pause_begin = sample
            elif not state and pause_begin:
                pauses.append([pause_begin, sample])
        elif 'lap' in sample.events:
            laps.append(sample)
        else:
            filtered_events.append(sample)

    model = {}
    model['move'] = move
    model['samples'] = samples
    model['events'] = filtered_events
    model['pauses'] = pauses
    model['laps'] = laps
    model['gps_samples'] = [sample for sample in samples if sample.sample_type and sample.sample_type.startswith('gps-')]
    if 'swimming' in move.activity:
        swimming_events = [sample for sample in filtered_events if 'swimming' in sample.events]
        model['swimming_events'] = swimming_events

        model['swimming_style_changes'] = [sample for sample in swimming_events if sample.events['swimming']['type'] == 'StyleChange']
        model['swimming_turns'] = [sample for sample in swimming_events if sample.events['swimming']['type'] == 'Turn']

        swimming_strokes = [sample for sample in swimming_events if sample.events['swimming']['type'] == 'Stroke']
        model['swimming_strokes'] = swimming_strokes

        pause_samples = list(itertools.chain.from_iterable(pauses))
        model['swimming_strokes_and_pauses'] = sorted(swimming_strokes + pause_samples, key=lambda sample: sample.time)

        model['swim_pace'] = timedelta(seconds=move.duration.total_seconds() / move.distance)

        assert len(model['swimming_strokes']) == move.stroke_count

    # eg. 'Pool swimming' → 'pool_swimming'
    activity_name = move.activity.lower().replace(' ', '_')
    return render_template("move/%s.html" % activity_name, **model)

if __name__ == '__main__':
    manager.run()
