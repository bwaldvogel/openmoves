#!/usr/bin/env python

import xkcdpass.xkcd_password as xp
from flask_script import Command, Option

from imports import move_import
from model import db, User, Move, Sample


class AddUser(Command):
    """ Adds an user to the database """

    def __init__(self, app_context, app_bcrypt):
        super(AddUser, self).__init__()
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

            if user.password is not str:
                user.password = user.password.decode('utf-8')

            user.active = True
            db.session.add(user)
            db.session.commit()

            print("created user '%s' in '%s'" % (user.username, db.engine.url))


class ImportMove(Command):
    """ Imports a move to the database """

    def __init__(self, app_context):
        super(ImportMove, self).__init__()
        self.app_context = app_context

    def get_options(self):
        return [
            Option('--username', '-u', dest='username', required=True),
            Option('--filename', '-f', dest='filename', required=True),
        ]

    def run(self, username, filename):
        user = User.query.filter_by(username=username).one()
        with open(filename, 'r') as f:
            move = move_import(f, filename, user)
            if move:
                print("imported move %d" % move.id)


class DeleteMove(Command):
    """ Deletes a move from the database """

    def __init__(self, app_context):
        super(DeleteMove, self).__init__()
        self.app_context = app_context

    def get_options(self):
        return [
            Option('--moveid', '-m', dest='move_id', required=True),
        ]

    def run(self, move_id):
        move = Move.query.filter_by(id=move_id).one()
        Sample.query.filter_by(move=move).delete()
        db.session.delete(move)
        db.session.commit()
        print("deleted move %d" % move.id)


class ListMoves(Command):
    """ Lists all moves in the database """

    def __init__(self, app_context):
        super(ListMoves, self).__init__()
        self.app_context = app_context

    def get_options(self):
        return []

    def run(self):
        for move in Move.query:
            print("move %d: user=%s, date='%s', activity=%s" % (move.id, move.user.username, move.date_time, move.activity))
