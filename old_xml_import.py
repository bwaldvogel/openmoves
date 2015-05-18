#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask import flash
from model import db
from model import Move, Device
from lxml import objectify
import re
from _import import add_children, normalize_move, parse_samples, postprocess_move


def parse_move(tree):
    move = Move()
    add_children(move, tree.header)
    normalize_move(move)
    return move


def old_xml_import(xmlfile, user):
        filename = xmlfile.filename
        data = xmlfile.readlines()

        if isinstance(data[0], bytes):
            data = [str(x.decode('utf-8')) for x in data]

        data[0] = data[0] + "<sml>"
        data.append("</sml>")

        filematch = re.match(r'log-([A-F0-9]{16})-\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}-\d+\.xml', filename)
        if not filematch:
            flash("illegal filename: '%s'" % filename, 'error')
            return

        serial_number = filematch.group(1)

        tree = objectify.fromstring("\n".join(data).encode('utf-8'))
        move = parse_move(tree)
        move.source = filename
        move.import_module = __name__

        device = Device.query.filter_by(serial_number=serial_number).scalar()
        if not device:
            device = Device()
            device.serial_number = serial_number
            db.session.add(device)

        if Move.query.filter_by(user=user, date_time=move.date_time, device=device).scalar():
            flash("%s at %s already exists" % (move.activity, move.date_time), 'warning')
        else:
            move.user = user
            move.device = device
            db.session.add(move)

            for sample in parse_samples(tree.Samples.iterchildren(), move):
                db.session.add(sample)
            postprocess_move(move)
            db.session.commit()
            return move
