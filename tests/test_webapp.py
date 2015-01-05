# vim: set fileencoding=utf-8 :

import webapp
from create_schema import create_schema
from recreate_schema import recreate_schema
from create_user import create_user
from model import db, User
import pytest
import html5lib

app = None


class TestWebapp(object):

    @classmethod
    def setup_class(cls):
        global app
        app = webapp.init(configFile=None)
        db_uri = 'sqlite:///:memory:'
        app.config.update(SQLALCHEMY_ECHO=False, WTF_CSRF_ENABLED=False, DEBUG=True, TESTING=True, SQLALCHEMY_DATABASE_URI=db_uri)

    def setup_method(self, method):
        self.app = app
        self.client = app.test_client()

    def _login(self):
        data = {'username': 'test_user', 'password': 'test password'}
        self.client.post('/login', data=data, follow_redirects=True)

    def _validateResponse(self, response, tmpdir=None, code=200, checkContent=True):
        assert response.status_code == code, "HTTP status: %s" % response.status
        if tmpdir:
            tmpdir.join("response.html").write(response.data, mode='wb')

        if checkContent:
            self._validateHtml5(response)

    def _validateHtml5(self, response):
        parser = html5lib.HTMLParser(strict=True)
        parser.parse(response.data)

    def _assertRequiresLogin(self, url):
        expectedUrl = 'login?next=%s' % url.replace('/', '%2F')
        return self._assertRedirects(url, expectedUrl, code=302)

    def _assertRedirects(self, url, location, code=301, **requestargs):
        response = self.client.get("%s" % url, **requestargs)
        assert response.status_code == code
        if location.startswith("/"):
            location = location[1:]
        assert response.headers["Location"] == "http://localhost/%s" % location

    def test_create_schema(self):
        create_schema(app)

    def test_recreate_schema(self):
        recreate_schema(app)

    def test_create_user(self):
        with app.test_request_context():
            assert User.query.count() == 0
        create_user(app, username='test_user')
        with app.test_request_context():
            assert User.query.count() == 1
            assert User.query.filter_by(username='test_user').one()

        with pytest.raises(AssertionError) as e:
            create_user(app, username='test_user')
        assert "user already exists" in str(e.value)

        create_user(app, username='test_user2')
        with app.test_request_context():
            assert User.query.count() == 2
            assert User.query.filter_by(username='test_user').one() != User.query.filter_by(username='test_user2').one()

    def test_index(self, tmpdir):
        response = self.client.get('/')
        self._validateResponse(response, tmpdir)
        assert "An open source alternative" in str(response.data)
        assert "0 moves already analyzed" in str(response.data)

    def test_login_get(self, tmpdir):
        response = self.client.get('/login')
        self._validateResponse(response, tmpdir)
        assert u"<title>OpenMoves – Login</title>" in response.data.decode('utf-8')
        assert u"Please sign in" in response.data.decode('utf-8')

    def test_login_invalid(self, tmpdir):
        data = {'username': 'user which does not exist', 'password': 'test password'}
        response = self.client.post('/login', data=data)
        self._validateResponse(response, tmpdir)
        assert "no such user" in str(response.data)
        assert "Please sign in" in str(response.data)

    def test_login_valid(self, tmpdir):

        with app.test_request_context():
            User.query.delete(synchronize_session=False)
            db.session.commit()

        create_user(app, username='test_user', password='test password')

        data = {'username': 'test_user', 'password': 'test password'}
        response = self.client.post('/login', data=data, follow_redirects=True)
        self._validateResponse(response, tmpdir)
        assert u"<title>OpenMoves – Moves</title>" in response.data.decode('utf-8')

    def test_moves_not_logged_in(self, tmpdir):
        self._assertRequiresLogin('/moves')

    def test_moves_empty(self, tmpdir):
        self._login()
        response = self.client.get('/moves')
        self._validateResponse(response, tmpdir)
        assert u"<title>OpenMoves – Moves</title>" in response.data.decode('utf-8')
        assert u"<h3>0 Moves</h3>" in response.data.decode('utf-8')

    def test_move_not_logged_in(self, tmpdir):
        self._assertRequiresLogin('/moves/1')

    def test_move_not_found(self, tmpdir):
        self._login()
        response = self.client.get('/moves/1')
        self._validateResponse(response, code=404, checkContent=False)

    def test_dashboard_not_logged_in(self, tmpdir):
        self._assertRequiresLogin('/dashboard')

    def test_dashboard_empty(self, tmpdir):
        self._login()
        response = self.client.get('/dashboard')
        self._validateResponse(response, tmpdir)
        assert u"<title>OpenMoves – Dashboard</title>" in response.data.decode('utf-8')

    def test_export_move_not_found(self, tmpdir):
        self._login()
        response = self.client.get('/moves/1/export')
        self._validateResponse(response, code=404, checkContent=False)

    def test_export_move_not_logged_in(self, tmpdir):
        self._assertRequiresLogin('/moves/1/export')
