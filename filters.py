#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from datetime import timedelta
import math
import time


def dateTime(time):
    return time.strftime("%Y-%m-%d %H:%M:%S")


def dateTimeMillis(date):
    return date.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def duration(value):
    if isinstance(value, str):
        value = timedelta(seconds=float(value))
    elif isinstance(value, float) or isinstance(value, int):
        value = timedelta(seconds=float(value))

    hours, remainder = divmod(value.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return '%02d:%02d:%05.2f' % (hours, minutes, seconds)


def radianToDegree(value):
    return 180.0 / math.pi * value


def unixEpoch(date):
    return 1000 * time.mktime(date.timetuple())


def register_filters(app):
    app.jinja_env.filters['dateTime'] = dateTime
    app.jinja_env.filters['dateTimeMillis'] = dateTimeMillis
    app.jinja_env.filters['duration'] = duration
    app.jinja_env.filters['degree'] = radianToDegree
    app.jinja_env.filters['epoch'] = unixEpoch
