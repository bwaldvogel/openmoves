#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from datetime import timedelta
import math
import time


def format_date_time(time):
    return time.strftime("%Y-%m-%d %H:%M:%S")


def format_date_time_millis(date):
    return date.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def duration(value):
    if type(value).__name__ in ('str', 'unicode'):
        value = timedelta(seconds=float(value))
    elif isinstance(value, (float, int)):
        value = timedelta(seconds=float(value))

    hours, remainder = divmod(value.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return '%02d:%02d:%05.2f' % (hours, minutes, seconds)


def swim_pace(value):
    assert isinstance(value, timedelta)
    hours, remainder = divmod(100 * value.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    assert hours == 0
    return '%02d:%05.2f min / 100 m' % (minutes, seconds)


def radian_to_degree(value):
    return 180.0 / math.pi * value


def unix_epoch(date):
    return 1000 * time.mktime(date.timetuple())


def register_filters(app):
    app.jinja_env.filters['date_time'] = format_date_time
    app.jinja_env.filters['date_time_millis'] = format_date_time_millis
    app.jinja_env.filters['duration'] = duration
    app.jinja_env.filters['degree'] = radian_to_degree
    app.jinja_env.filters['epoch'] = unix_epoch
    app.jinja_env.filters['swim_pace'] = swim_pace
