#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask import flash
from model import db
from model import Move, Device, Sample
from lxml import objectify
import re
from _import import add_children, set_attr, parse_json, normalize_move, normalize_tag


def parse_move(tree):
    move = Move()
    add_children(move, tree.header)
    normalize_move(move)
    return move


def parse_samples(tree, move):
    for sample_node in tree.Samples.iterchildren():
        sample = Sample()
        sample.move = move

        for child in sample_node.iterchildren():
            tag = normalize_tag(child.tag)
            value = child.text

            if tag in ['utc', 'ehpe', 'hr']:
                set_attr(sample, tag, value)
            elif tag.startswith('gps'):
                tag = tag[0:3].lower() + tag[3:]
                set_attr(sample, tag, value)
            elif tag == 'events':
                sample.events = parse_json(child)
            elif tag == 'satellites':
                sample.satellites = parse_json(child)
            elif tag == 'apps_data':
                sample.apps_data = parse_json(child)
            else:
                set_attr(sample, tag, value)

        yield sample


def old_xml_import(xmlfile, user):
        filename = xmlfile.filename
        data = xmlfile.readlines()

        if isinstance(data[0], bytes):
            data = [str(x.decode('utf-8')) for x in data]

        data[0] = data[0] + "<sml>"
        data.append("</sml>")

        filematch = re.match(r"log-([A-F0-9]{16})-\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}-\d+\.xml", filename)
        if not filematch:
            flash("illegal filename: '%s'" % filename, 'error')
            return

        serial_number = filematch.group(1)

        tree = objectify.fromstring("\n".join(data).encode('utf-8'))
        move = parse_move(tree)
        move.source = filename
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

            for sample in parse_samples(tree, move):
                db.session.add(sample)
            db.session.commit()
            return move
