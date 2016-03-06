#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask import flash
from model import db
from model import Move, Device
from lxml import objectify
import os
from _import import add_children, set_attr, normalize_tag, normalize_move, parse_samples, postprocess_move


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


def sml_import(xmlfile, user, request_form):
    filename = xmlfile.filename
    tree = objectify.parse(xmlfile).getroot()
    move = parse_move(tree)
    move.source = os.path.abspath(filename)
    move.import_module = __name__
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

    if Move.query.filter_by(user=user, date_time=move.date_time, device=device).scalar():
        flash("%s at %s already exists" % (move.activity, move.date_time), 'warning')
    else:
        move.user = user
        move.device = device
        postprocess_move(move)
        db.session.add(move)

        samples = tree.DeviceLog.Samples.iterchildren()
        for sample in parse_samples(samples, move):
            db.session.add(sample)
        db.session.commit()
        return move
