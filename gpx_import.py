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
from numpy import mean

GPX_DEVICE_NAME = 'GPX import'
GPX_DEVICE_SERIAL = 'GPX_IMPORT'

GPX_1_0_NAMESPACE = '{http://www.topografix.com/GPX/1/0}'
GPX_1_1_NAMESPACE = '{http://www.topografix.com/GPX/1/1}'

GPX_TRK = 'trk'
GPX_TRKSEG = 'trkseg'
GPX_TRKPT = 'trkpt'
GPX_TRKPT_ATTRIB_LATITUDE = 'lat'
GPX_TRKPT_ATTRIB_LONGITUDE = 'lon'
GPX_TRKPT_ATTRIB_ELEVATION = 'ele'

GPX_NAMESPACE_TRACKPOINTEXTENSION_V1 = '{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}'
GPX_EXTENSION_TRACKPOINTEXTENSION = 'TrackPointExtension'
GPX_EXTENSION_TRACKPOINTEXTENSION_HEARTRATE = 'hr'

GPX_EXTENSION_GPX_V1_TEMP = 'temp'
GPX_EXTENSION_GPX_V1_DISTANCE = 'distance'
GPX_EXTENSION_GPX_V1_ALTITUDE = 'altitude'
GPX_EXTENSION_GPX_V1_ENERGY = 'energy'
GPX_EXTENSION_GPX_V1_SEALEVELPRESSURE = 'seaLevelPressure'
GPX_EXTENSION_GPX_V1_SPEED = 'speed'
GPX_EXTENSION_GPX_V1_VSPEED = 'verticalSpeed'


def parse_sample_extensions(sample, track_point, gpx_namespace):
    if hasattr(track_point, 'extensions'):
        for extension in track_point.extensions.iterchildren():
            if extension.tag == GPX_NAMESPACE_TRACKPOINTEXTENSION_V1 + GPX_EXTENSION_TRACKPOINTEXTENSION:
                if hasattr(extension, GPX_EXTENSION_TRACKPOINTEXTENSION_HEARTRATE):
                    sample.hr = float(extension.hr) / 60.0  # BPM
            elif extension.tag == gpx_namespace + GPX_EXTENSION_GPX_V1_TEMP:
                sample.temperature = float(extension.text) + 273.15  # Kelvin
            elif extension.tag == gpx_namespace + GPX_EXTENSION_GPX_V1_DISTANCE:
                sample.distance = float(extension.text)
            elif extension.tag == gpx_namespace + GPX_EXTENSION_GPX_V1_ALTITUDE:
                sample.gps_altitude = float(extension.text)
                sample.altitude = int(round(sample.gps_altitude))
            elif extension.tag == gpx_namespace + GPX_EXTENSION_GPX_V1_ENERGY:
                sample.energy_consumption = float(extension.text)
            elif extension.tag == gpx_namespace + GPX_EXTENSION_GPX_V1_SEALEVELPRESSURE:
                sample.sea_level_pressure = float(extension.text)
            elif extension.tag == gpx_namespace + GPX_EXTENSION_GPX_V1_SPEED:
                sample.speed = float(extension.text)
            elif extension.tag == gpx_namespace + GPX_EXTENSION_GPX_V1_VSPEED:
                sample.vertical_speed = float(extension.text)


def parse_samples(tree, move, gpx_namespace):
    all_samples = []

    tracks = tree.iterchildren(tag=gpx_namespace + GPX_TRK)
    for track in tracks:
        track_samples = []

        track_segments = track.iterchildren(tag=gpx_namespace + GPX_TRKSEG)
        for track_segment in track_segments:
            segment_samples = []

            track_points = track_segment.iterchildren(tag=gpx_namespace + GPX_TRKPT)
            for track_point in track_points:
                sample = Sample()
                sample.move = move

                # GPS position / altitude
                sample.latitude = degree_to_radian(float(track_point.attrib[GPX_TRKPT_ATTRIB_LATITUDE]))
                sample.longitude = degree_to_radian(float(track_point.attrib[GPX_TRKPT_ATTRIB_LONGITUDE]))
                sample.sample_type = 'gps-base'
                if hasattr(track_point, GPX_TRKPT_ATTRIB_ELEVATION):
                    sample.gps_altitude = float(track_point.ele)
                    sample.altitude = int(round(sample.gps_altitude))

                # Time / UTC
                sample.utc = dateutil.parser.parse(str(track_point.time))
                if len(segment_samples) > 0:
                    # Accumulate time delta to previous sample to get the total duration
                    time_delta = sample.utc - segment_samples[-1].utc
                    sample.time = segment_samples[-1].time + time_delta

                    # Accumulate distance to previous sample
                    distance_delta = vincenty((radian_to_degree(sample.latitude), radian_to_degree(sample.longitude)),
                                              (radian_to_degree(segment_samples[-1].latitude), radian_to_degree(segment_samples[-1].longitude))).meters
                    sample.distance = segment_samples[-1].distance + distance_delta
                    sample.speed = distance_delta / time_delta.total_seconds()

                elif len(track_samples) > 0:
                    sample.time = track_samples[-1].time
                    sample.distance = track_samples[-1].distance
                    sample.speed = track_samples[-1].speed
                elif len(all_samples) > 0:
                    sample.time = all_samples[-1].time
                    sample.distance = all_samples[-1].distance
                    sample.speed = all_samples[-1].speed
                else:
                    sample.time = timedelta(0)
                    sample.distance = 0
                    sample.speed = 0

                parse_sample_extensions(sample, track_point, gpx_namespace)
                segment_samples.append(sample)

            # Insert an pause event between every tracksegment
            insert_pause(track_samples, segment_samples)
            track_samples.extend(segment_samples)

        # Insert an pause event between every track
        insert_pause(all_samples, track_samples)
        all_samples.extend(track_samples)
    return all_samples


def insert_pause(start_pause_samples, end_pause_samples):
    if (len(start_pause_samples) > 0 and len(end_pause_samples) > 0):
        # {"pause": {"state": "True", "duration": "724.1", "distance": "2576", "type": "30"}}
        start_pause_samples[-1].events = {"pause": {"state": "True"}}
        # {"pause": {"state": "False", "duration": "0", "distance": "0", "type": "31"}}
        end_pause_samples[0].events = {"pause": {"state": "False"}}


def parse_move(tree):
    move = Move()
    move.activity = 'Unknown activity'
    move.import_date_time = datetime.now()

    return move


def parse_device(tree):
    device = Device()
    device.name = GPX_DEVICE_NAME
    device.serial_number = GPX_DEVICE_SERIAL
    return device


def derive_move_infos_from_samples(move, samples):
    if len(samples) > 0:
        move.date_time = samples[0].utc
        move.log_item_count = len(samples)

        # Duration / Speed / Distance
        move.duration = samples[-1].time
        move.distance = samples[-1].distance
        move.speed_avg = move.distance / move.duration.total_seconds()
        move.speed_max = max(sample.speed for sample in samples)

        # Altitudes
        altitudes = [sample.altitude for sample in samples if sample.altitude]  # hasattr(sample, 'altitude')]
        if len(altitudes) > 0:
            move.altitude_min = min(altitudes)
            move.altitude_max = max(altitudes)

        # Temperature
        temperatures = [sample.temperature for sample in samples if sample.temperature]
        if len(temperatures) > 0:
            move.temperature_min = min(temperatures)
            move.temperature_max = max(temperatures)

        # Heart rate
        hrs = [sample.hr for sample in samples if sample.hr]
        if len(hrs) > 0:
            move.hr_min = min(hrs)
            move.hr_max = max(hrs)
            move.hr_avg = mean(hrs)


def gpx_import(xmlfile, user):
    filename = xmlfile.filename
    tree = objectify.parse(xmlfile).getroot()

    if(tree.tag.startswith(GPX_1_0_NAMESPACE)):
        gpx_namespace = GPX_1_0_NAMESPACE
    elif(tree.tag.startswith(GPX_1_1_NAMESPACE)):
        gpx_namespace = GPX_1_1_NAMESPACE
    else:
        flash("Unsupported GPX format version: %s" % tree.tag)

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
    all_samples = parse_samples(tree, move, gpx_namespace)

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
