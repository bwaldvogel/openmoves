#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask_login import LoginManager
from flask_wtf import Form
from model import User
from wtforms import TextField, PasswordField

login_manager = LoginManager()


class LoginForm(Form):
    username = TextField()
    password = PasswordField()


@login_manager.user_loader
def load_user(username):
    return User.query.filter_by(username=username).scalar()
