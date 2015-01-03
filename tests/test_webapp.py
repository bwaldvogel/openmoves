# vim: set fileencoding=utf-8 :

import webapp

app = None


class TestWebapp(object):

    @classmethod
    def setup_class(cls):
        global app
        app = webapp.init()
        db_uri = 'sqlite:///:memory:'
        app.config.update(SQLALCHEMY_ECHO=False, TESTING=True, SQLALCHEMY_DATABASE_URI=db_uri)
