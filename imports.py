#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask import flash

from old_xml_import import old_xml_import
from sml_import import sml_import
from gpx_import import gpx_import
import gzip
from model import db, Sample
from sqlalchemy.sql import func


def move_import(xmlfile, filename, user):
    if filename.endswith('.gz'):
        xmlfile = gzip.GzipFile(fileobj=xmlfile, mode='rb', filename=filename)
        filename = filename[:-len('.gz')]

    if filename.endswith('.xml'):
        move = old_xml_import(xmlfile, user)
    elif filename.endswith('.sml'):
        move = sml_import(xmlfile, user)
    elif filename.endswith('.gpx'):
        move = gpx_import(xmlfile, user)
    else:
        flash("unknown fileformat: '%s'" % xmlfile.filename, 'error')
        move = None

    if move:
        move.temperature_avg, = db.session.query(func.avg(Sample.temperature)).filter(Sample.move == move, Sample.temperature > 0).one()

        stroke_count = 0
        for events, in db.session.query(Sample.events).filter(Sample.move == move, Sample.events != None):
            if 'swimming' in events and events['swimming']['type'] == 'Stroke':
                stroke_count += 1

        if 'swimming' in move.activity:
            assert stroke_count > 0

        if stroke_count > 0:
            move.stroke_count = stroke_count

        db.session.commit()
        return move
