# vim: set fileencoding=utf-8 :

import webapp
from create_schema import create_schema
from recreate_schema import recreate_schema
from create_user import create_user
from model import User
import pytest
import html5lib

app = None


class TestWebapp(object):

    @classmethod
    def setup_class(cls):
        global app
        app = webapp.init()
        db_uri = 'sqlite:///:memory:'
        app.config.update(SQLALCHEMY_ECHO=False, DEBUG=True, TESTING=True, SQLALCHEMY_DATABASE_URI=db_uri)

    def _validateResponse(self, response, tmpdir, code=200, checkContent=True):
        assert response.status_code == code, "HTTP status: %s" % response.status
        tmpdir.join("response.html").write(response.data)

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
        response = app.test_client().get('/')
        self._validateResponse(response, tmpdir)
        assert "An open source alternative" in str(response.data)
        assert "0 moves already analyzed" in str(response.data)
