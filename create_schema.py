#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import webapp
from model import db


def create_schema(app):
    with app.app_context():
        db.create_all()
        print("created schema for '%s'" % app.config['SQLALCHEMY_DATABASE_URI'])


if __name__ == "__main__":
    app = webapp.init()
    app.config.update(SQLALCHEMY_ECHO=False)
    create_schema(app)
