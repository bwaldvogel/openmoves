#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import webapp
from model import db


def recreate_schema(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("recreated schema for '%s'" % app.config['SQLALCHEMY_DATABASE_URI'])


if __name__ == "__main__":
    app = webapp.init()
    app.config.update(SQLALCHEMY_ECHO=False)
    recreate_schema(app)
