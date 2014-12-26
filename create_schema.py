#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import webapp
from model import db

app = webapp.init()
app.config.update(SQLALCHEMY_ECHO=False)

with app.app_context():
    db.create_all()
    print("created schema for '%s'" % app.config['SQLALCHEMY_DATABASE_URI'])
