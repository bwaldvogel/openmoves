# vim: set fileencoding=utf-8 :

import openmoves
from commands import AddUser
from model import db, User, Move, MoveEdit
from flask import json
import pytest
import html5lib
import re
import os

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
        data = {'username': username, 'password': password}
        return self.client.post('/login', data=data, follow_redirects=True)

    def _validate_response(self, response, tmpdir=None, code=200, check_content=True):
        assert response.status_code == code, "HTTP status: %s" % response.status
        if tmpdir:
            tmpdir.join("response.html").write(response.data, mode='wb')

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

            user = User(username=username)
            user.password = openmoves.app_bcrypt.generate_password_hash(password, 10)
            user.active = True
            db.session.add(user)
            db.session.commit()

        response = self._login()
        response_data = self._validate_response(response, tmpdir)
        assert u"<title>OpenMoves – Moves</title>" in response_data

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
        assert u'All moves <span class="badge">0</span>' in response_data

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
        response = self.client.get('/dashboard?start_date=2014-01-01&end_date=2017-01-01')
        response_data = self._validate_response(response, tmpdir)
        assert u'<title>OpenMoves – Dashboard</title>' in response_data
        assert u'<tr><th>Total Distance</th><td>0.000 km</td></tr>' in response_data
        assert u'<tr><th>Total Time</th><td>0:00:00 h</td></tr>' in response_data

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

    def test_moves(self, tmpdir):
        self._login()
        response = self.client.get('/moves')
        response_data = self._validate_response(response, tmpdir)

        assert u'<title>OpenMoves – Moves</title>' in response_data
        assert u'<td><a href="/moves/1">2014-11-09 14:55:13</a></td>' in response_data

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
            move.location_raw = {'address':{'city_district': u'Galtür', 'country_code': 'at'}}
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

        response_data = self._validate_response(response, tmpdir)
        assert u'<title>OpenMoves – Move 4</title>' in response_data
        assert u'>Kayaking</' in response_data
        assert u'<th>Avg. Heart Rate</th>' in response_data
        assert u'<td><span>97 bpm</span></td>' in response_data

        response = self.client.get('/moves')
        response_data = self._validate_response(response, tmpdir)
        assert re.search(u'<th><a href="/moves.+?">Heart Rate</a></th>', response_data)
        assert u'<td><span>97 bpm</span></td>' in response_data

    def test_activity_types_not_logged_in(self, tmpdir):
        self._assert_requires_login('/activity_types')

    def test_activity_types(self, tmpdir):
        self._login()

        response = self.client.get('/activity_types')
        response_data = self._validate_response(response, tmpdir)

        expected_activities = ('Cycling', 'Kayaking', 'Pool swimming', 'Trekking')
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

    def test_delete_moves(self, tmpdir):
        self._login()
        with app.test_request_context():
            total_moves_before = Move.query.count()
            assert total_moves_before > 0

            for idx, move in enumerate(Move.query):
                response = self.client.get("/moves/%d/delete" % move.id, follow_redirects=True)
                response_data = self._validate_response(response)
                assert u'<title>OpenMoves – Moves</title>' in response_data

                total_moves = Move.query.count()
                assert total_moves == total_moves_before - (idx + 1)
                assert u"All moves <span class=\"badge\">%d</span>" % total_moves in response_data

            total_moves = Move.query.count()
            assert total_moves == 0
