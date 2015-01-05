#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask import flash
from model import db
from model import Move, Device, Sample
from lxml import objectify
import os
from _import import addChildren, setAttr, normalizeTag, parseJson, normalizeMove
from flask.ext.login import current_user


def parseMove(tree):
    deviceLog = tree.DeviceLog
    move = Move()

    addChildren(move, deviceLog.Header)

    for child in deviceLog.Device.Info.iterchildren():
        tag = normalizeTag(child.tag)
        attr = "deviceInfo%s" % tag
        setAttr(move, attr, child.text)

    normalizeMove(move)
    return move


def parseDevice(tree):
    device = Device()
    device.name = tree.DeviceLog.Device.Name.text
    device.serialNumber = tree.DeviceLog.Device.SerialNumber.text
    return device


def parseSamples(tree, move):
    for sampleNode in tree.DeviceLog.Samples.iterchildren():
        sample = Sample()
        sample.move = move
        sample.events = None

        for child in sampleNode.iterchildren():
            tag = normalizeTag(child.tag)
            value = child.text

            if tag in ['UTC', 'EHPE', 'HR']:
                tag = tag.lower()
                setAttr(sample, tag, value)
            elif tag.startswith('GPS'):
                tag = tag[0:3].lower() + tag[3:]
                setAttr(sample, tag, value)
            elif tag == 'Events':
                sample.events = parseJson(child)
            elif tag == 'Satellites':
                sample.satellites = parseJson(child)
            elif tag == 'AppsData':
                sample.appsData = parseJson(child)
            else:
                tag = tag[0].lower() + tag[1:]
                setAttr(sample, tag, value)

        yield sample


def smlImport(xmlfile):
        filename = xmlfile.filename

        tree = objectify.parse(xmlfile).getroot()
        move = parseMove(tree)
        move.source = os.path.abspath(filename)
        device = parseDevice(tree)
        persistentDevice = Device.query.filter_by(serialNumber=device.serialNumber).scalar()
        if persistentDevice:
            if not persistentDevice.name:
                flash("update device name to '%s'" % device.name)
                persistentDevice.name = device.name
            else:
                assert device.name == persistentDevice.name
            device = persistentDevice
        else:
            db.session.add(device)

        if Move.query.filter_by(user=current_user, dateTime=move.dateTime, device=device).scalar():
            flash("%s at %s already exists" % (move.activity, move.dateTime), 'warning')
        else:
            move.user = current_user
            move.device = device
            db.session.add(move)

            for sample in parseSamples(tree, move):
                db.session.add(sample)
            db.session.commit()
            return move
