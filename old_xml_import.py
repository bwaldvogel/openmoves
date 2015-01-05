#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask import flash
from model import db
from model import Move, Device, Sample
from lxml import objectify
import re
from _import import addChildren, setAttr, parseJson, normalizeMove
from flask.ext.login import current_user


def parseMove(tree):
    move = Move()
    addChildren(move, tree.header)
    normalizeMove(move)
    return move


def parseSamples(tree, move):
    for sampleNode in tree.Samples.iterchildren():
        sample = Sample()
        sample.move = move

        for child in sampleNode.iterchildren():
            tag = child.tag
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


def oldXmlImport(xmlfile):
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

        serialNumber = filematch.group(1)

        tree = objectify.fromstring("\n".join(data).encode('utf-8'))
        move = parseMove(tree)
        move.source = filename
        device = Device.query.filter_by(serialNumber=serialNumber).scalar()
        if not device:
            device = Device()
            device.serialNumber = serialNumber
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
