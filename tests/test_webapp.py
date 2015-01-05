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

    def _validateResponse(self, response, tmpdir, code=200, checkContent=True):
        assert response.status_code == code, "HTTP status: %s" % response.status
        tmpdir.join("response.html").write(response.data, mode='wb')

        if checkContent:
            self._validateHtml5(response)

    def _validateHtml5(self, response):
        parser = html5lib.HTMLParser(strict=True)
        parser.parse(response.data)

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
        assert "Please sign in" in str(response.data)

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

    def test_moves_empty(self, tmpdir):
        self._login()
        response = self.client.get('/moves')
        self._validateResponse(response, tmpdir)
        assert u"<title>OpenMoves – Moves</title>" in response.data.decode('utf-8')
        assert u"<h3>0 Moves</h3>" in response.data.decode('utf-8')

    def test_dashboard_empty(self, tmpdir):
        self._login()
        response = self.client.get('/dashboard')
        self._validateResponse(response, tmpdir)
        assert u"<title>OpenMoves – Dashboard</title>" in response.data.decode('utf-8')
