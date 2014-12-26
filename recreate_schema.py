#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import webapp
from model import db

app = webapp.init()

with app.app_context():
    db.drop_all()
    db.create_all()
