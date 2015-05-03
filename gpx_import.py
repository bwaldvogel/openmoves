#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import os
import dateutil.parser
from flask import flash
from model import db, Device, Move, Sample
from lxml import objectify
from filters import degree_to_radian, radian_to_degree
from datetime import datetime, timedelta
from _import import postprocess_move
from geopy.distance import vincenty

GPX_1_0_NAMESPACE = '{http://www.topografix.com/GPX/1/0}'
GPX_1_1_NAMESPACE = '{http://www.topografix.com/GPX/1/1}'
GPX_NAMESPACE_TRACKPOINTEXTENSION_V1 = '{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}'

GPX_1_1_TAG_TRK = GPX_1_1_NAMESPACE + 'trk'
GPX_1_1_TAG_TRKSEG = GPX_1_1_NAMESPACE + 'trkseg'
GPX_1_1_TAG_TRKPT = GPX_1_1_NAMESPACE + 'trkpt'
GPX_1_1_TAG_TRKPT_ATTRIB_LATITUDE = 'lat'
GPX_1_1_TAG_TRKPT_ATTRIB_LONGITUDE = 'lon'

GPX_EXTENSION_TRACKPOINTEXTENSION = GPX_NAMESPACE_TRACKPOINTEXTENSION_V1 + 'TrackPointExtension'
GPX_EXTENSION_GPX_V1_TEMP = GPX_1_0_NAMESPACE + 'temp'
GPX_EXTENSION_GPX_V1_DISTANCE = GPX_1_0_NAMESPACE + 'distance'
GPX_EXTENSION_GPX_V1_ALTITUDE = GPX_1_0_NAMESPACE + 'altitude'
GPX_EXTENSION_GPX_V1_ENERGY = GPX_1_0_NAMESPACE + 'energy'
GPX_EXTENSION_GPX_V1_SEALEVELPRESSURE = GPX_1_0_NAMESPACE + 'seaLevelPressure'
GPX_EXTENSION_GPX_V1_SPEED = GPX_1_0_NAMESPACE + 'speed'
GPX_EXTENSION_GPX_V1_VSPEED = GPX_1_0_NAMESPACE + 'verticalSpeed'

def parse_sample_extensions(sample, track_point):
    if hasattr(track_point, 'extensions'):
        for extension in track_point.extensions.iterchildren():
            if extension.tag == GPX_EXTENSION_TRACKPOINTEXTENSION:
                if hasattr(extension, 'hr'):
                    sample.hr = float(extension.hr)
            elif extension.tag == GPX_EXTENSION_GPX_V1_TEMP:
                sample.temp = float(extension.text)
            elif extension.tag == GPX_EXTENSION_GPX_V1_DISTANCE:
                sample.distance = float(extension.text)
            elif extension.tag == GPX_EXTENSION_GPX_V1_ALTITUDE:
                sample.gps_altitude = float(extension.text)
                sample.altitude = int(round(sample.gps_altitude))
            elif extension.tag == GPX_EXTENSION_GPX_V1_ENERGY:
                sample.energy_consumption = float(extension.text)
            elif extension.tag == GPX_EXTENSION_GPX_V1_SEALEVELPRESSURE:
                sample.sea_level_pressure = float(extension.text)
            elif extension.tag == GPX_EXTENSION_GPX_V1_SPEED:
                sample.speed = float(extension.text)
            elif extension.tag == GPX_EXTENSION_GPX_V1_VSPEED:
                sample.vertical_speed = float(extension.text)

def parse_samples(tree, move):
    gpx_samples = []

    tracks = tree.iterchildren(tag=GPX_1_1_TAG_TRK)
    for track in tracks:
        track_samples = []

        track_segments = track.iterchildren(tag=GPX_1_1_TAG_TRKSEG)
        for track_segment in track_segments:
            segment_samples = []

            track_points = track_segment.iterchildren(tag=GPX_1_1_TAG_TRKPT)
            for track_point in track_points:
                sample = Sample()
                sample.move = move

                # GPS position / altitude
                sample.latitude = degree_to_radian(float(track_point.attrib['lat']))
                sample.longitude = degree_to_radian(float(track_point.attrib['lon']))
                sample.sample_type = 'gps-base'
                sample.gps_altitude = float(track_point.ele)
                sample.altitude = int(round(sample.gps_altitude))

                # Time / UTC
                sample.utc = dateutil.parser.parse(str(track_point.time))
                if len(segment_samples) > 0:
                    sample.time = segment_samples[-1].time + (sample.utc - segment_samples[-1].utc)  # Calculate time delta to previous sample

                    vincenty_distance = vincenty((radian_to_degree(sample.latitude), radian_to_degree(sample.longitude)),
                                                 (radian_to_degree(segment_samples[-1].latitude), radian_to_degree(segment_samples[-1].longitude))).meters
                    sample.distance = segment_samples[-1].distance + vincenty_distance

                elif len(track_samples) > 0:
                    sample.time = track_samples[-1].time
                    sample.distance = track_samples[-1].distance
                elif len(gpx_samples) > 0:
                    sample.time = gpx_samples[-1].time
                    sample.distance = gpx_samples[-1].distance
                else:
                    sample.time = timedelta(0)
                    sample.distance = 0

                # Extensions
                parse_sample_extensions(sample, track_point)

                segment_samples.append(sample)
            track_samples.extend(segment_samples)
        gpx_samples.extend(track_samples)

        return gpx_samples

def parse_move(tree):
    gpx_track = tree.trk
    move = Move()
    move.activity = 'Unknown activity'
    move.import_date_time = datetime.now()

    move.distance = 0
    move.ascent_time = timedelta(hours=1)
    move.descent_time = timedelta(hours=1)

    return move

def parse_device(tree):
    device = Device()
    device.name = "GPX import"
    device.serial_number = "GPX_IMPORT"
    return device

def derive_move_infos_from_samples(move, samples):
    if len(samples) > 0:
        move.date_time = samples[0].utc

        # Duration / Distance / Average speed
        move.duration = samples[-1].time
        move.distance = samples[-1].distance
        move.speed_avg = move.distance / move.duration.total_seconds()

def gpx_import(xmlfile, user):
    filename = xmlfile.filename
    tree = objectify.parse(xmlfile).getroot()
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
    move = parse_move(tree)
    move.source = os.path.abspath(filename)

    # Parse samples
    all_samples = parse_samples(tree, move)

    derive_move_infos_from_samples(move, all_samples)

    if Move.query.filter_by(user=user, date_time=move.date_time, device=device).scalar():
        flash("%s at %s already exists" % (move.activity, move.date_time), 'warning')
    else:
        move.user = user
        move.device = device
        db.session.add(move)

        for sample in all_samples:
            db.session.add(sample)

        postprocess_move(move)
        db.session.commit()
        return move
