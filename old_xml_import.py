#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask import flash
from model import db
from model import LogEntry, Device, Sample
from lxml import objectify
import re
from _import import addChildren, setAttr, parseJson, normalizeLogEntry
from flask.ext.login import current_user


def parseLogEntry(tree):
    logEntry = LogEntry()
    addChildren(logEntry, tree.header)
    normalizeLogEntry(logEntry)
    return logEntry


def parseSamples(tree, logEntry):
    for sampleNode in tree.Samples.iterchildren():
        sample = Sample()
        sample.logEntry = logEntry

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

        data[0] = data[0] + "<sml>"
        data.append("</sml>")

        filematch = re.match(r"log-([A-F0-9]{16})-\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}-\d+\.xml", filename)
        if not filematch:
            flash("illegal filename: '%s'" % filename, 'error')
            return

        serialNumber = filematch.group(1)

        tree = objectify.fromstring("\n".join(data))
        logEntry = parseLogEntry(tree)
        logEntry.source = filename
        device = Device.query.filter_by(serialNumber=serialNumber).scalar()
        if not device:
            flash("found no device with serial number: '%s'" % serialNumber, 'error')
            return

        if LogEntry.query.filter_by(user=current_user, dateTime=logEntry.dateTime, device=device).scalar():
            flash("%s at %s already exists" % (logEntry.activity, logEntry.dateTime), 'warning')
        else:
            logEntry.user = current_user
            logEntry.device = device
            db.session.add(logEntry)

            for sample in parseSamples(tree, logEntry):
                db.session.add(sample)
            db.session.commit()
            return logEntry
