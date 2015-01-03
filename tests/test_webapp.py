# vim: set fileencoding=utf-8 :

import webapp
from create_schema import create_schema
from recreate_schema import recreate_schema

app = None


class TestWebapp(object):

    @classmethod
    def setup_class(cls):
        global app
        app = webapp.init()
        db_uri = 'sqlite:///:memory:'
        app.config.update(SQLALCHEMY_ECHO=False, TESTING=True, SQLALCHEMY_DATABASE_URI=db_uri)

    def test_create_schema(self):
        create_schema(app)

    def test_recreate_schema(self):
        recreate_schema(app)
