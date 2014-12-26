#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import webapp
from model import db, User
import sys
from webapp import app_bcrypt
import xkcdpass.xkcd_password as xp

app = webapp.init()
app.config.update(SQLALCHEMY_ECHO=False)

if len(sys.argv) != 2:
    print("usage: %s <username>" % sys.argv[0])
    sys.exit(1)

username = sys.argv[1]

with app.app_context():
    wordfile = xp.locate_wordfile()
    mywords = xp.generate_wordlist(wordfile=wordfile, min_length=5, max_length=8)
    password = xp.generate_xkcdpassword(mywords, acrostic="ambit")

    assert not User.query.filter_by(username=username).scalar(), "user already exists"

    user = User(username=username)
    user.password = app_bcrypt.generate_password_hash(password, 10)
    user.active = True
    db.session.add(user)
    db.session.commit()
    print("created user '%s'" % user.username)
    print("generated password: '%s'" % password)
