#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask_login import LoginManager
from flask_wtf import Form
from wtforms import StringField, PasswordField

from model import User

login_manager = LoginManager()


class LoginForm(Form):
    username = StringField()
    password = PasswordField()


@login_manager.user_loader
def load_user(username):
    return User.query.filter_by(username=username).scalar()
