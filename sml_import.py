#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from flask import flash
from model import db
from model import LogEntry, Device, Sample
from lxml import objectify
import os
from _import import addChildren, setAttr, normalizeTag, parseJson, normalizeLogEntry
from flask.ext.login import current_user


def parseLogEntry(tree):
    deviceLog = tree.DeviceLog
    logEntry = LogEntry()

    addChildren(logEntry, deviceLog.Header)

    for child in deviceLog.Device.Info.iterchildren():
        tag = normalizeTag(child.tag)
        attr = "deviceInfo%s" % tag
        setAttr(logEntry, attr, child.text)

    normalizeLogEntry(logEntry)
    return logEntry


def parseDevice(tree):
    device = Device()
    device.name = tree.DeviceLog.Device.Name.text
    device.serialNumber = tree.DeviceLog.Device.SerialNumber.text
    return device


def parseSamples(tree, logEntry):
    for sampleNode in tree.DeviceLog.Samples.iterchildren():
        sample = Sample()
        sample.logEntry = logEntry
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
        logEntry = parseLogEntry(tree)
        logEntry.source = os.path.abspath(filename)
        device = parseDevice(tree)
        persistentDevice = Device.query.filter_by(serialNumber=device.serialNumber).scalar()
        if persistentDevice:
            device = persistentDevice
        else:
            db.session.add(device)

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
