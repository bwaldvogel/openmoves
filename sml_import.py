#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask import flash
from model import db
from model import Move, Device, Sample
from lxml import objectify
import os
from _import import add_children, set_attr, normalize_tag, parse_json, normalize_move
from flask.ext.login import current_user


def parse_move(tree):
    device_log = tree.DeviceLog
    move = Move()

    add_children(move, device_log.Header)

    for child in device_log.Device.Info.iterchildren():
        tag = normalize_tag(child.tag)
        attr = "device_info_%s" % tag.lower()
        set_attr(move, attr, child.text)

    normalize_move(move)
    return move


def parse_device(tree):
    device = Device()
    device.name = tree.DeviceLog.Device.Name.text
    device.serial_number = tree.DeviceLog.Device.SerialNumber.text
    return device


def parse_samples(tree, move):
    for sample_node in tree.DeviceLog.Samples.iterchildren():
        sample = Sample()
        sample.move = move
        sample.events = None

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


def sml_import(xmlfile):
        filename = xmlfile.filename
        tree = objectify.parse(xmlfile).getroot()
        move = parse_move(tree)
        move.source = os.path.abspath(filename)
        device = parse_device(tree)
        persistent_device = Device.query.filter_by(serial_number=device.serial_number).scalar()
        if persistent_device:
            if not persistent_device.name:
                flash("update device name to '%s'" % device.name)
                persistent_device.name = device.name
            else:
                assert device.name == persistent_device.name
            device = persistent_device
        else:
            db.session.add(device)

        if Move.query.filter_by(user=current_user, date_time=move.date_time, device=device).scalar():
            flash("%s at %s already exists" % (move.activity, move.date_time), 'warning')
        else:
            move.user = current_user
            move.device = device
            db.session.add(move)

            for sample in parse_samples(tree, move):
                db.session.add(sample)
            db.session.commit()
            return move
