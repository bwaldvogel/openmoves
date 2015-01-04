# vim: set fileencoding=utf-8 :

import webapp
from create_schema import create_schema
from recreate_schema import recreate_schema
from create_user import create_user
from model import User
import pytest

app = None


class TestWebapp(object):

    @classmethod
    def setup_class(cls):
        global app
        app = webapp.init()
        db_uri = 'sqlite:///:memory:'
        app.config.update(SQLALCHEMY_ECHO=False, DEBUG=True, TESTING=True, SQLALCHEMY_DATABASE_URI=db_uri)

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
