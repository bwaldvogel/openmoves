# vim: set fileencoding=utf-8 :

import openmoves
from commands import AddUser
from model import db, User, Move, MoveEdit
from flask import json
import pytest
import html5lib
import re
import os
from datetime import timedelta, datetime
from gpx_import import GPX_IMPORT_OPTION_PAUSE_DETECTION, GPX_IMPORT_OPTION_PAUSE_DETECTION_THRESHOLD, GPX_DEVICE_NAME, \
    GPX_ACTIVITY_TYPE, GPX_DEVICE_SERIAL, GPX_SAMPLE_TYPE, GPX_TRK, GPX_IMPORT_PAUSE_TYPE_PAUSE_DETECTION


app = None


class TestOpenMoves(object):

    @classmethod
    def setup_class(cls):
        global app
        app = openmoves.init(configfile=None)
        db_uri = 'sqlite:///:memory:'
        app.config.update(SQLALCHEMY_ECHO=False, WTF_CSRF_ENABLED=False, DEBUG=True, TESTING=True, SQLALCHEMY_DATABASE_URI=db_uri, SECRET_KEY="testing")

    def setup_method(self, method):
        self.app = app
        self.client = app.test_client()

    def _login(self, username='test_user', password='test password'):
        data = {'username': username, 'password': password, 'timezone': 'Europe/Berlin'}
        return self.client.post('/login', data=data, follow_redirects=True)

    def _validate_response(self, response, tmpdir=None, code=200, check_content=True):
        if tmpdir:
            tmpdir.join("response.html").write(response.data, mode='wb')

        assert response.status_code == code, "HTTP status: %s" % response.status

        if response.data:
            response_data = response.data.decode('utf-8')

        if check_content:
            if response.mimetype == 'text/html':
                self._validate_html5(response_data)
            elif response.mimetype == 'application/json':
                return json.loads(response_data)
            else:
                raise ValueError("illegal mimetype: '%s'" % response.mimetype)

        return response_data

    def _validate_html5(self, response_data):
        parser = html5lib.HTMLParser(strict=True)
        parser.parse(response_data)

    def _assert_requires_login(self, url, method='GET'):
        expected_url = 'login?next=%s' % url.replace('/', '%2F')
        return self._assert_redirects(url, expected_url, code=302, method=method)

    def _assert_redirects(self, url, location, code=301, method='GET', **requestargs):
        if method == 'GET':
            response = self.client.get(url, **requestargs)
        elif method == 'POST':
            response = self.client.post(url, **requestargs)
        else:
            raise ValueError("illegal method: %s" % method)

        assert response.status_code == code
        if location.startswith("/"):
            location = location[1:]
        assert response.headers["Location"] == "http://localhost/%s" % location

    def test_initialize_config(self, tmpdir):
        tmpfile = tmpdir.join("openmoves.cfg")
        openmoves.initialize_config(tmpfile)
        lines = tmpfile.readlines()
        assert len(lines) == 1
        assert re.match(r"SECRET_KEY = '[a-f0-9]{64}'", lines[0]), "unexpected line: %s" % lines[0]

    def test_initialize_config_subsequent_calls_differ(self, tmpdir):

        tmpfile1 = tmpdir.join("openmoves1.cfg")
        tmpfile2 = tmpdir.join("openmoves2.cfg")
        openmoves.initialize_config(tmpfile1)
        openmoves.initialize_config(tmpfile2)

        assert tmpfile1.read() != tmpfile2.read()

    def test_create_schema(self):
        with app.test_request_context():
            db.create_all()

    def test_add_user(self):
        with app.test_request_context():
            assert User.query.count() == 0

        cmd = AddUser(lambda: app.app_context(), app_bcrypt=openmoves.app_bcrypt)
        cmd.run(username='test_user')

        with app.test_request_context():
            assert User.query.count() == 1
            assert User.query.filter_by(username='test_user').one()

        with pytest.raises(AssertionError) as e:
            cmd.run(username='test_user')
        assert u"user already exists" in str(e.value)

        cmd.run(username='test_user2')
        with app.test_request_context():
            assert User.query.count() == 2
            assert User.query.filter_by(username='test_user').one() != User.query.filter_by(username='test_user2').one()

    def test_index(self, tmpdir):
        response = self.client.get('/')
        response_data = response_data = self._validate_response(response, tmpdir)
        assert u"An open source alternative" in response_data
        assert u"0 moves already analyzed" in response_data

    def test_login_get(self, tmpdir):
        response = self.client.get('/login')
        response_data = self._validate_response(response, tmpdir)
        assert u"<title>OpenMoves – Login</title>" in response_data
        assert u"Please sign in" in response_data

    def test_login_invalid(self, tmpdir):
        data = {'username': 'user which does not exist', 'password': 'test password'}
        response = self.client.post('/login', data=data)
        response_data = self._validate_response(response, tmpdir)
        assert u"no such user" in response_data
        assert u"Please sign in" in response_data

    def test_login_valid(self, tmpdir):

        username = 'test_user'
        password = 'test password'

        with app.test_request_context():
            User.query.delete(synchronize_session=False)

            user = User(username=username, active=True)
            user.password = openmoves.app_bcrypt.generate_password_hash(password, 10)
            db.session.add(user)
            db.session.commit()

        response = self._login()
        response_data = self._validate_response(response, tmpdir)
        assert u"<title>OpenMoves – Dashboard</title>" in response_data

    def test_login_logout_other_user(self, tmpdir):

        username = 'other_user'
        password = u'Paßswörd→✓≈'

        with app.test_request_context():
            user = User(username=username, active=True)
            user.password = openmoves.app_bcrypt.generate_password_hash(password, 10)
            db.session.add(user)
            db.session.commit()

        response = self._login(username=username, password=password)
        response_data = self._validate_response(response, tmpdir)
        assert u'<title>OpenMoves – Dashboard</title>' in response_data
        assert username in response_data

        response = self.client.get('/logout', follow_redirects=True)
        response_data = self._validate_response(response, tmpdir)
        assert u'<title>OpenMoves</title>' in response_data
        assert username not in response_data

    def test_custom_404(self, tmpdir):
        response = self.client.get('/page-which-does-not-exist')
        response_data = self._validate_response(response, tmpdir, code=404, check_content=True)
        assert u"<title>OpenMoves – Not found</title>" in response_data

    def test_moves_not_logged_in(self, tmpdir):
        self._assert_requires_login('/moves')

    def test_moves_empty(self, tmpdir):
        self._login()
        response = self.client.get('/moves')
        response_data = self._validate_response(response, tmpdir)
        assert u"<title>OpenMoves – Moves</title>" in response_data
        assert u'No moves in selected date range' in response_data

    def test_move_not_logged_in(self, tmpdir):
        self._assert_requires_login('/moves/1')

    def test_move_not_found(self, tmpdir):
        self._login()
        response = self.client.get('/moves/1')
        self._validate_response(response, code=404, check_content=False)

    def test_delete_move_not_logged_in(self, tmpdir):
        self._assert_requires_login('/moves/1/delete')

    def test_delete_move_not_found(self, tmpdir):
        self._login()
        response = self.client.get('/moves/1/delete')
        self._validate_response(response, code=404, check_content=False)

    def test_dashboard_not_logged_in(self, tmpdir):
        self._assert_requires_login('/dashboard')

    def test_dashboard_empty(self, tmpdir):
        self._login()
        response = self.client.get('/dashboard')
        response_data = self._validate_response(response, tmpdir)
        assert u'<title>OpenMoves – Dashboard</title>' in response_data

    def test_export_move_not_found(self, tmpdir):
        self._login()
        response = self.client.get('/moves/1/export')
        self._validate_response(response, code=404, check_content=False)

    def test_export_move_not_logged_in(self, tmpdir):
        self._assert_requires_login('/moves/1/export')

    def test_import_move(self, tmpdir):
        self._login()
        response = self.client.get('/import')
        response_data = self._validate_response(response, tmpdir)
        assert u'<title>OpenMoves – Import</title>' in response_data
        assert 'Please find' in response_data
        assert '%AppData%/Suunto/Moveslink2' in response_data

    def test_import_move_upload_single(self, tmpdir):
        self._login()
        data = {}

        filename = 'CAFEBABECAFEBABE-2014-11-09T14_55_13-0.sml.gz'
        dn = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dn, filename), 'rb') as f:
            data['files'] = [(f, filename)]
            response = self.client.post('/import', data=data, follow_redirects=True)

        response_data = self._validate_response(response, tmpdir)
        assert u'<title>OpenMoves – Move 1</title>' in response_data
        assert u"imported &#39;%s&#39;: move 1" % filename in response_data
        assert u'>Pool swimming</' in response_data
        assert u'<td>2014-11-09 14:55:13</td>' in response_data
        assert u'<td>02:07.80 min / 100 m</td>' in response_data
        assert u'<td>795</td>' in response_data  # strokes
        # first pause
        assert u'<span class="date-time">2014-11-09 15:15:49.991</span>' in response_data
        assert u'<span class="date-time">2014-11-09 15:26:45.314</span>' in response_data
        assert u'<td>00:10:55.32</td>' in response_data

        with app.test_request_context():
            move = Move.query.one()
            assert move.recovery_time is None

    def test_import_move_upload_multiple(self, tmpdir):
        self._login()
        data = {}

        dn = os.path.dirname(os.path.realpath(__file__))
        filename1 = 'CAFEBABECAFEBABE-2014-12-31T12_00_32-0.sml.gz'
        filename2 = 'log-CAFEBABECAFEBABE-2014-07-23T18_56_14-5.xml.gz'
        with open(os.path.join(dn, filename1), 'rb') as file1:
            with open(os.path.join(dn, filename2), 'rb') as file2:
                data['files'] = [(file1, filename1), (file2, filename2)]
                response = self.client.post('/import', data=data, follow_redirects=True)
        response_data = self._validate_response(response, tmpdir)

        assert u'<title>OpenMoves – Moves</title>' in response_data
        assert u'imported 2 moves' in response_data

        with app.test_request_context():
            move = Move.query.filter(Move.activity == 'Trekking').one()
            assert move.ascent_time == timedelta(seconds=1181)

            move = Move.query.filter(Move.activity == 'Cycling').one()
            assert move.distance == 21277

    def test_import_move_upload_gpx(self, tmpdir):
        self._login()
        data = {}

        filename = 'baerensee_testtrack.gpx'
        # filename = 'Move_2013_07_21_15_26_53_Trail+running.gpx.gz'
        dn = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dn, filename), 'rb') as f:
            data['files'] = [(f, filename)]
            response = self.client.post('/import', data=data, follow_redirects=True)

        with app.test_request_context():
            count = Move.query.count()

        response_data = self._validate_response(response, tmpdir)
        assert u"<title>OpenMoves – Move %d</title>" % count in response_data
        assert u'imported' in response_data
        assert filename in response_data

        with app.test_request_context():
            move = Move.query.filter(Move.activity == GPX_ACTIVITY_TYPE).one()
            assert move.device.name == GPX_DEVICE_NAME
            assert move.device.serial_number == GPX_DEVICE_SERIAL
            assert move.activity == GPX_ACTIVITY_TYPE
            assert move.date_time == datetime(2015, 1, 1, 10, 0, 0 , 0)
            assert move.duration == timedelta(minutes=18)
            assert int(move.distance) == 1800
            assert move.log_item_count == 8 + 2  # 2 entries for the pause events
            assert move.log_item_count == move.samples.count()

            # Altitudes
            assert move.altitude_max == move.samples[4].altitude
            assert move.altitude_max == move.samples[4].gps_altitude
            assert move.altitude_min == move.samples[0].altitude
            assert move.altitude_min == move.samples[7].altitude
            assert move.ascent == 600
            assert move.descent == 1200
            assert move.ascent_time == timedelta(minutes=6) - timedelta(microseconds=1)
            assert move.descent_time == timedelta(minutes=12) - timedelta(microseconds=1)

            # Speed
            assert round(move.speed_avg, 1) == round(6 / 3.6, 1)
            assert round(move.speed_max, 1) == round(30 / 3.6, 1)
            assert move.speed_max == move.samples[5].speed

            # Pause events
            events = [sample for sample in move.samples if sample.events]
            assert len(events) == 2
            start_pause_sample = events[0].events['pause']
            assert start_pause_sample['state'].lower() == 'true'
            assert start_pause_sample['duration'] == str(timedelta(minutes=54))
            assert int(float(start_pause_sample['distance'])) == 142
            assert start_pause_sample['type'] == GPX_TRK

            end_pause_sample = events[1].events['pause']
            assert end_pause_sample['state'].lower() == 'false'
            assert end_pause_sample['duration'] == str(0)
            assert int(float(end_pause_sample['distance'])) == 0
            assert end_pause_sample['type'] == GPX_TRK

            # Temperatures
            assert round(move.temperature_min - 273.15, 1) == 17.0
            assert round(move.temperature_max - 273.15, 1) == 29.0
            # HR
            assert round(move.hr_max * 60.0, 1) == 210.0
            assert round(move.hr_min * 60.0, 1) == 50.0
            assert round(move.hr_avg * 60.0, 1) == 127.5

            previous_sample = None
            for sample in move.samples:
                if sample.sample_type != GPX_SAMPLE_TYPE:
                    continue
                assert sample.time >= timedelta(seconds=0)
                assert sample.utc == move.date_time + sample.time
                assert sample.distance >= 0
                assert sample.sea_level_pressure >= 100
                assert sample.sea_level_pressure <= 1035
                assert sample.temperature >= move.temperature_min
                assert sample.temperature <= move.temperature_max
                assert sample.energy_consumption >= 1.0
                assert sample.energy_consumption <= 2.0
                assert sample.speed >= 0.0
                assert round(sample.speed, 1) <= 30.0 / 3.6
                assert sample.vertical_speed >= 0.1
                assert sample.vertical_speed <= 0.6

                if previous_sample:
                    assert sample.time > previous_sample.time
                    assert sample.utc > previous_sample.utc
                    assert sample.distance >= previous_sample.distance

                previous_sample = sample

        # Finally delete the GPX import for next GPX import test with pause detection
        response_delete = self.client.get('/moves/%d/delete' % count, follow_redirects=True)
        response_delete_data = self._validate_response(response_delete, tmpdir)
        assert u"move %d deleted" % count in response_delete_data


    def test_import_move_upload_gpx_with_pause_detection(self, tmpdir):
        """GPX import with pause detection option"""
        self._login()
        data = {}

        filename = 'baerensee_testtrack.gpx'
        # filename = 'Move_2013_07_21_15_26_53_Trail+running.gpx.gz'
        dn = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dn, filename), 'rb') as f:
            data['files'] = [(f, filename)]
            data[GPX_IMPORT_OPTION_PAUSE_DETECTION] = 'on'
            data[GPX_IMPORT_OPTION_PAUSE_DETECTION_THRESHOLD] = '479'
            response = self.client.post('/import', data=data, follow_redirects=True)

        with app.test_request_context():
            count = Move.query.count()

        response_data = self._validate_response(response, tmpdir)
        assert u"<title>OpenMoves – Move %d</title>" % count in response_data
        assert u'imported' in response_data
        assert filename in response_data

        with app.test_request_context():
            move = Move.query.filter(Move.activity == GPX_ACTIVITY_TYPE).one()
            assert move.device.name == GPX_DEVICE_NAME
            assert move.device.serial_number == GPX_DEVICE_SERIAL
            assert move.date_time == datetime(2015, 1, 1, 10, 0, 0 , 0)
            assert move.duration == timedelta(minutes=18 - 8)  # 8min by pause detection
            assert int(move.distance) == 1800 - 400  # 400m by pause detection
            assert move.log_item_count == 8 + 4  # 4 entries for the pause events
            assert move.log_item_count == move.samples.count()

            # Attention: samples are not sorted by UTC
            assert move.altitude_max == move.samples[4].altitude
            assert move.altitude_max == move.samples[4].gps_altitude
            assert move.altitude_min == move.samples[0].altitude
            assert move.altitude_min == move.samples[9].altitude
            assert move.ascent == 600
            assert move.descent == 1200 - 400  # 400m by pause_detection
            assert move.ascent_time == timedelta(minutes=6) - timedelta(microseconds=1)
            assert move.descent_time == timedelta(minutes=(12 - 8)) - timedelta(microseconds=1 + 2)  # 8min by pause detection

            # Speed
            assert round(move.speed_avg, 1) == round(8.4 / 3.6, 1)
            assert round(move.speed_max, 1) == round(30 / 3.6, 1)
            assert move.speed_max == move.samples[5].speed

            # Pause events
            events = [sample for sample in move.samples if sample.events]
            assert len(events) == 2 + 2  # 2 pauses by pause_detection
            start_pause_sample = events[2].events['pause']
            assert start_pause_sample['state'].lower() == 'true'
            assert start_pause_sample['duration'] == str(timedelta(minutes=54))
            assert int(float(start_pause_sample['distance'])) == 142
            assert start_pause_sample['type'] == GPX_TRK

            end_pause_sample = events[3].events['pause']
            assert end_pause_sample['state'].lower() == 'false'
            assert end_pause_sample['duration'] == str(0)
            assert int(float(end_pause_sample['distance'])) == 0
            assert end_pause_sample['type'] == GPX_TRK

            start_pause_sample = events[0].events['pause']
            assert start_pause_sample['state'].lower() == 'true'
            assert start_pause_sample['duration'] == str(timedelta(minutes=8))  # 8min by pause detection
            assert int(float(start_pause_sample['distance'])) == 400
            assert start_pause_sample['type'] == GPX_IMPORT_PAUSE_TYPE_PAUSE_DETECTION

            end_pause_sample = events[1].events['pause']
            assert end_pause_sample['state'].lower() == 'false'
            assert end_pause_sample['duration'] == str(0)
            assert int(float(end_pause_sample['distance'])) == 0
            assert end_pause_sample['type'] == GPX_IMPORT_PAUSE_TYPE_PAUSE_DETECTION

    def test_import_move_already_exists(self, tmpdir):
        self._login()
        data = {}

        with app.test_request_context():
            count_before = Move.query.count()

        filename = 'baerensee_testtrack.gpx'
        dn = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dn, filename), 'rb') as f:
            data['files'] = [(f, filename)]
            response = self.client.post('/import', data=data, follow_redirects=True)

        with app.test_request_context():
            count_after = Move.query.count()

        assert count_after == count_before

        response_data = self._validate_response(response, tmpdir)
        assert u'<title>OpenMoves – Import</title>' in response_data
        assert u'already exists' in response_data

    def test_moves(self, tmpdir):
        self._login()
        response = self.client.get('/moves?start_date=2014-01-01&end_date=2014-12-31')
        response_data = self._validate_response(response, tmpdir)

        assert u'<title>OpenMoves – Moves</title>' in response_data
        assert u'<td><a href="/moves/1">2014-11-09 14:55:13</a></td>' in response_data
        assert u'<td><a href="/moves/2">2014-12-31 12:00:32</a></td>' in response_data
        assert u'<td><a href="/moves/3">2014-07-23 18:56:14</a></td>' in response_data

        assert u'All moves <span class="badge">3</span>' in response_data
        assert u'Cycling <span class="badge">1</span>' in response_data
        assert u'Trekking <span class="badge">1</span>' in response_data
        assert u'Pool swimming <span class="badge">1</span>' in response_data

        assert u'>Pool swimming</' in response_data
        assert u'<td>00:31:25.00</td>' in response_data
        assert u'<td>1475 m</td>' in response_data
        assert u'<td><span>2.8 km/h</span></td>' in response_data
        assert u'<td><span>27.4°C</span></td>' in response_data
        assert u'<td>795</td>' in response_data

    def test_moves_with_date_range(self, tmpdir):
        self._login()

        response = self.client.get('/moves?start_date=2014-11-09&end_date=2014-11-09')
        response_data = self._validate_response(response, tmpdir)
        assert u'<td><a href="/moves/1">2014-11-09 14:55:13</a></td>' in response_data
        assert u'All moves <span class="badge">1</span>' in response_data
        assert u'Pool swimming <span class="badge">1</span>' in response_data
        assert u'Cycling' not in response_data
        assert u'Trekking' not in response_data

        response = self.client.get('/moves?start_date=2014-07-01&end_date=2014-12-01')
        response_data = self._validate_response(response, tmpdir)
        assert u'<td><a href="/moves/1">2014-11-09 14:55:13</a></td>' in response_data
        assert u'<td><a href="/moves/3">2014-07-23 18:56:14</a></td>' in response_data
        assert u'All moves <span class="badge">2</span>' in response_data
        assert u'Cycling <span class="badge">1</span>' in response_data
        assert u'Pool swimming <span class="badge">1</span>' in response_data
        assert u'Trekking' not in response_data

    def test_move_pages(self, tmpdir):
        self._login()
        with app.test_request_context():
            for move in Move.query:
                response = self.client.get("/moves/%d" % move.id)
                response_data = self._validate_response(response, tmpdir)
                assert u"<title>OpenMoves – Move %d</title>" % move.id in response_data
                assert u">%s</" % move.activity in response_data

    def test_csv_export_filename(self, tmpdir):
        self._login()
        response = self.client.get('/moves/1/export?format=csv')
        assert response.headers['Content-Disposition'] == 'attachment; filename=Move_2014-11-09T14_55_13_Pool+swimming.csv'

        response = self.client.get('/moves/2/export?format=csv')
        assert response.headers['Content-Disposition'] == 'attachment; filename=Move_2014-12-31T12_00_32_DE_Stegen_Trekking.csv'

    def test_csv_exports(self, tmpdir):
        self._login()
        with app.test_request_context():
            for move in Move.query:
                response = self.client.get("/moves/%d/export?format=csv" % move.id)
                response_data = self._validate_response(response, tmpdir, check_content=False)
                lines = response_data.split('\r\n')
                header = lines[0]
                assert 'Timestamp;Duration;Latitude' in header
                assert len(lines) == move.samples.count() + 1

    def test_gpx_export(self, tmpdir):
        self._login()
        response = self.client.get('/moves/3/export?format=gpx')
        response_data = self._validate_response(response, tmpdir, check_content=False)
        assert response.headers['Content-Disposition'] == 'attachment; filename=Move_2014-07-23T18_56_14_DE_Rheinbach_Cycling.gpx'
        assert u'<gpx ' in response_data
        assert u'lat="50.632' in response_data
        assert u'lon="6.952' in response_data

    def test_gpx_export_umlaut_in_filename(self, tmpdir):
        with app.test_request_context():
            move = Move.query.filter(Move.id == 3).one()
            move.location_raw = {'address': {'city_district': u'Galtür', 'country_code': 'at'}}
            db.session.commit()

        self._login()
        response = self.client.get('/moves/3/export?format=gpx')
        assert response.headers['Content-Disposition'] == u'attachment; filename=Move_2014-07-23T18_56_14_AT_Galt%C3%BCr_Cycling.gpx'

    def test_move_with_heart_rate(self, tmpdir):
        self._login()
        data = {}

        filename = 'CAFEBABECAFEBABE-2014-11-02T13_08_09-0.sml.gz'
        dn = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dn, filename), 'rb') as f:
            data['files'] = [(f, filename)]
            response = self.client.post('/import', data=data, follow_redirects=True)

        with app.test_request_context():
            count = Move.query.count()

        response_data = self._validate_response(response, tmpdir)
        assert u"<title>OpenMoves – Move %d</title>" % count in response_data
        assert u'>Kayaking</' in response_data
        assert u'<th>Avg. Heart Rate</th>' in response_data
        assert u'<td><span>97 bpm</span></td>' in response_data

        response = self.client.get('/moves?start_date=2014-01-01&end_date=2020-01-01')
        response_data = self._validate_response(response, tmpdir)
        assert re.search(u'<th><a href="/moves.+?">Heart Rate</a></th>', response_data)
        assert u'<td><span>97 bpm</span></td>' in response_data

    def test_import_move_with_relative_performance_level(self, tmpdir):
        self._login()
        data = {}

        filename = 'BABECAFEBABECAFE-2015-06-25T18_45_58-0.sml.gz'
        dn = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dn, filename), 'rb') as f:
            data['files'] = [(f, filename)]
            response = self.client.post('/import', data=data, follow_redirects=True)

        with app.test_request_context():
            count = Move.query.count()

        response_data = self._validate_response(response, tmpdir)
        assert u"<title>OpenMoves – Move %d</title>" % count in response_data
        assert u'>Running</' in response_data
        assert filename in response_data

    def test_activity_types_not_logged_in(self, tmpdir):
        self._assert_requires_login('/activity_types')

    def test_activity_types(self, tmpdir):
        self._login()

        response = self.client.get('/activity_types')
        response_data = self._validate_response(response, tmpdir)

        expected_activities = ('Cycling', 'Kayaking', 'Pool swimming', 'Running', 'Trekking', 'Unknown activity')
        expected_data = [{"text": activity, "value": activity} for activity in expected_activities]

        assert response_data == expected_data

    def test_edit_move_not_logged_in(self, tmpdir):
        self._assert_requires_login("/moves/1", method='POST')

    def test_edit_move_illegal_name(self, tmpdir):
        self._login()

        data = {'name': 'some illegal name', 'pk': 1}
        with pytest.raises(ValueError) as e:
            self.client.post('/moves/1', data=data)
        assert u"illegal name" in str(e.value)

    def test_dashboard_all_moves(self, tmpdir):
        self._login()
        response = self.client.get('/dashboard?start_date=2014-01-01&end_date=2014-12-31')
        response_data = self._validate_response(response, tmpdir)
        assert u'<title>OpenMoves – Dashboard</title>' in response_data
        assert u'>#Moves<' in response_data
        assert u'>4<' in response_data
        assert u'<th>Total Distance</th><td>33.55 km</td>' in response_data
        assert u'<th>Total Duration</th><td>03:47:09.60</td>' in response_data
        assert u'<th>Total Average</th>' in response_data
        assert u'<th>Total Ascent</th><td>110 m</td>' in response_data
        assert u'<th>Total Descent</th><td>218 m</td>' in response_data

    def test_dashboard_with_date_range(self, tmpdir):
        self._login()
        response = self.client.get('/dashboard?start_date=2014-08-01&end_date=2014-12-01')
        response_data = self._validate_response(response, tmpdir)
        assert u'<title>OpenMoves – Dashboard</title>' in response_data
        assert u'>#Moves<' in response_data
        assert u'>2<' in response_data
        assert u'<th>Total Distance</th><td>10.05 km</td>' in response_data
        assert u'<th>Total Duration</th><td>02:20:23.30</td>' in response_data

    def test_edit_move_different_user(self, tmpdir):
        username = 'some different user'
        password = 'some other password'
        with app.test_request_context():
            user = User(username=username, active=True)
            user.password = openmoves.app_bcrypt.generate_password_hash(password, 10)
            db.session.add(user)
            db.session.commit()

        self._login(username=username, password=password)

        data = {'name': 'activity', 'pk': 1}
        response = self.client.post('/moves/1', data=data)
        assert response.status_code == 404

    def test_edit_move_activity_illegal_value(self, tmpdir):
        self._login()

        data = {'name': 'activity', 'pk': 1, 'value': 'illegal activity'}
        with pytest.raises(ValueError) as e:
            self.client.post('/moves/1', data=data)
        assert u"illegal activity" in str(e.value)

    def test_edit_move_activity_success(self, tmpdir):
        self._login()

        data = {'name': 'activity', 'pk': 1, 'value': 'Trekking'}
        response = self.client.post('/moves/1', data=data)
        response_data = self._validate_response(response, check_content=False)
        assert response_data == 'OK'

        with app.test_request_context():
            move_edit = MoveEdit.query.one()
            assert move_edit.date_time
            assert move_edit.move_id == 1
            assert move_edit.old_value == {'activity': 'Pool swimming', 'activity_type': 6}
            assert move_edit.new_value == {'activity': 'Trekking', 'activity_type': 11}

    def test_delete_moves_batch(self, tmpdir):
        self._login()
        with app.test_request_context():
            total_moves_before = Move.query.count()
            assert total_moves_before > 2

            ids = [str(move.id) for move in Move.query[:2]]
            self.client.get("/moves/%s/delete" % ','.join(ids), follow_redirects=False)

            response = self.client.get('/moves?start_date=2013-01-01&end_date=2020-01-01')
            response_data = self._validate_response(response, tmpdir)
            assert u'<title>OpenMoves – Moves</title>' in response_data

            total_moves = Move.query.count()
            assert total_moves == total_moves_before - len(ids)
            assert u"All moves <span class=\"badge\">%d</span>" % total_moves in response_data

    def test_delete_moves(self, tmpdir):
        self._login()
        with app.test_request_context():
            total_moves_before = Move.query.count()
            assert total_moves_before > 0

            for idx, move in enumerate(Move.query):
                self.client.get("/moves/%d/delete" % move.id, follow_redirects=False)

                response = self.client.get('/moves?start_date=2013-01-01&end_date=2020-01-01')
                response_data = self._validate_response(response, tmpdir)
                assert u'<title>OpenMoves – Moves</title>' in response_data

                total_moves = Move.query.count()
                assert total_moves == total_moves_before - (idx + 1)
                if total_moves > 0:
                    assert u"All moves <span class=\"badge\">%d</span>" % total_moves in response_data
                else:
                    assert u'No moves in selected date range.' in response_data

            total_moves = Move.query.count()
            assert total_moves == 0
