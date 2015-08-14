#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask import flash

from old_xml_import import old_xml_import
from sml_import import sml_import
from gpx_import import gpx_import
import gzip
from model import db, Sample
from sqlalchemy.sql import func


def move_import(xmlfile, filename, user, request_form):
    if filename.endswith('.gz'):
        xmlfile = gzip.GzipFile(fileobj=xmlfile, mode='rb', filename=filename)
        filename = filename[:-len('.gz')]

    extension = filename[-4:]
    import_functions = {
        '.xml': old_xml_import,
        '.sml': sml_import,
        '.gpx': gpx_import,
    }

    if extension not in import_functions:
        flash("unknown fileformat: '%s'" % xmlfile.filename, 'error')
    else:
        import_function = import_functions[extension]
        move = import_function(xmlfile, user, request_form)
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
