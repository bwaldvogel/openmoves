#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask_script import Command, Option, prompt_bool
import xkcdpass.xkcd_password as xp
from model import db, User


class AddUser(Command):
    """ Adds an user to the database """

    def __init__(self, app_context, app_bcrypt):
        self.app_context = app_context
        self.app_bcrypt = app_bcrypt

    def get_options(self):
        return [
            Option('--username', '-u', dest='username', required=True),
            Option('--password', '-p', dest='password', required=False),
        ]

    def run(self, username, password=None):
        with self.app_context():
            if not password:
                wordfile = xp.locate_wordfile()
                mywords = xp.generate_wordlist(wordfile=wordfile, min_length=5, max_length=8)
                password = xp.generate_xkcdpassword(mywords, acrostic="ambit")
                print("generated password: '%s'" % password)

            assert not User.query.filter_by(username=username).scalar(), "user already exists"

            user = User(username=username)
            user.password = self.app_bcrypt.generate_password_hash(password, 10)
            user.active = True
            db.session.add(user)
            db.session.commit()

            print("created user '%s' in '%s'" % (user.username, db.engine.url))
