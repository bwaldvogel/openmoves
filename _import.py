# vim: set fileencoding=utf-8 :
import sqlalchemy
import re
from datetime import timedelta, datetime
from model import Sample
import numpy as np
from math import atan2
from filters import radian_to_degree
from geopy.geocoders import Nominatim
from geopy.distance import vincenty
import json
from flask import flash


# http://stackoverflow.com/questions/6671183/calculate-the-center-point-of-multiple-latitude-longitude-coordinate-pairs
def calculate_gps_center(gps_samples):
    coordinates = np.ndarray(shape=(len(gps_samples), 2), dtype=float)
    for idx, sample in enumerate(gps_samples):
        coordinates[idx][0] = sample.latitude
        coordinates[idx][1] = sample.longitude

    # Convert lat/lon (must be in radians) to Cartesian coordinates for each location.
    cos_lat = np.cos(coordinates[:, 0])
    sin_lat = np.sin(coordinates[:, 0])
    cos_lon = np.cos(coordinates[:, 1])
    sin_lon = np.sin(coordinates[:, 1])

    # Compute average x, y and z coordinates.
    x = np.average(cos_lat * cos_lon)
    y = np.average(cos_lat * sin_lon)
    z = np.average(sin_lat)

    # Convert average x, y, z coordinate to latitude and longitude.
    lon = atan2(y, x)
    hyp = np.sqrt(x * x + y * y)
    lat = atan2(z, hyp)

    center = (lat, lon)
    return center


def parse_samples(samples, move):
    for sample_node in samples:
        sample = Sample()
        sample.move = move

        for child in sample_node.iterchildren():
            tag = normalize_tag(child.tag)
            value = child.text

            if tag == 'events':
                sample.events = parse_json(child)
            elif tag == 'satellites':
                sample.satellites = parse_json(child)
            elif tag == 'apps_data':
                sample.apps_data = parse_json(child)
            else:
                set_attr(sample, tag, value)

        yield sample


def postprocess_move(move):
    gps_samples = [sample for sample in move.samples if sample.sample_type and sample.sample_type.startswith('gps-')]

    if gps_samples:
        gps_center = calculate_gps_center(gps_samples)
        move.gps_center_latitude = gps_center[0]
        move.gps_center_longitude = gps_center[1]

        gps_center_degrees = [radian_to_degree(x) for x in gps_center]

        gps_center_max_distance = 0
        for sample in gps_samples:
            point = (sample.latitude, sample.longitude)
            point_degrees = [radian_to_degree(x) for x in point]
            distance = vincenty(gps_center_degrees, point_degrees).meters
            gps_center_max_distance = max(gps_center_max_distance, distance)

        move.gps_center_max_distance = gps_center_max_distance

        first_sample = gps_samples[0]
        latitude = first_sample.latitude
        longitude = first_sample.longitude

        geolocator = Nominatim()
        location = geolocator.reverse("%f, %f" % (radian_to_degree(latitude), radian_to_degree(longitude)), timeout=60)
        move.location_address = location.address
        move.location_raw = location.raw


def normalize_move(move):

    move.import_date_time = datetime.now()

    if move.ascent_time.total_seconds() == 0:
        assert move.ascent == 0
        move.ascent = None

    if move.descent_time.total_seconds() == 0:
        assert float(move.descent) == 0
        move.descent = None

    if move.recovery_time.total_seconds() == 0:
        move.recovery_time = None

    if move.activity == 'Outdoor swimmin':
        move.activity = 'Outdoor swimming'


def remove_namespace(tag, ns='http://www.suunto.com/schemas/sml'):
    if tag.startswith('{'):
        ns = "{%s}" % ns
        assert tag.startswith(ns), "illegal tag: '%s'" % tag
        return tag[len(ns):]
    else:
        return tag


normalized_tags_cache = {}


def normalize_tag(tag):
    if tag in normalized_tags_cache:
        return normalized_tags_cache[tag]

    normalized_tag = remove_namespace(tag)

    # http://stackoverflow.com/a/1176023/4308
    normalized_tag = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', normalized_tag)
    normalized_tag = re.sub('([a-z0-9])([A-Z])', r'\1_\2', normalized_tag)
    normalized_tag = normalized_tag.lower()

    normalized_tags_cache[tag] = normalized_tag
    return normalized_tag


def _convert_attr(column_type, value, attr, message):
    if column_type == sqlalchemy.sql.sqltypes.Float:
        return float(value)
    elif column_type == sqlalchemy.sql.sqltypes.Interval:
        seconds = float(value)
        return timedelta(seconds=seconds)
    elif column_type == sqlalchemy.sql.sqltypes.Integer:
        if value == '0':
            return 0
        else:
            if value.startswith('0x'):
                return int(value, 16)
            else:
                return int(value, 10)

    elif column_type == sqlalchemy.sql.sqltypes.String:
        return value
    elif column_type == sqlalchemy.sql.sqltypes.DateTime:
        date, time = value.split('T')
        year, month, day = date.split('-')
        if time[-1] == 'Z':
            time = time[:-1]
        hour, minute, seconds = time.split(':')
        seconds = float(seconds)
        second = int(seconds)
        microsecond = int((seconds - second) * (10 ** 6))
        datetime_value = datetime(year=int(year),
                                  month=int(month),
                                  day=int(day),
                                  hour=int(hour),
                                  minute=int(minute),
                                  second=second,
                                  microsecond=microsecond)

        return datetime_value
    else:
        raise Exception("Unknown column type: %s for attribute '%s'" % (column_type, attr))


def set_attr(move, attr, value):
    prop = getattr(type(move), attr).property
    assert len(prop.columns) == 1

    value = _convert_attr(type(prop.columns[0].type), value, attr, "illegal value '%s' for '%s'" % (value, attr))
    setattr(move, attr, value)


def add_children(move, element):
    for child in element.iterchildren():
        tag = normalize_tag(child.tag)

        if tag in ('speed', 'hr', 'cadence', 'temperature', 'altitude'):
            for sub_child in child.iterchildren():
                sub_tag = tag + '_' + normalize_tag(sub_child.tag)
                set_attr(move, sub_tag, value=sub_child.text)
        else:
            set_attr(move, tag, value=child.text)


def _parse_recursive(node):
    if node.countchildren() > 0:
        events = {}
        for child in node.iterchildren():
            tag = remove_namespace(child.tag)
            if len(tag) > 2 and tag.upper() != tag:
                tag = tag[0].lower() + tag[1:]

            data = _parse_recursive(child)
            if tag in events:
                if not isinstance(events[tag], list):
                    events[tag] = [events[tag]]
                events[tag].append(data)
            else:
                events[tag] = data
        return events
    else:
        if len(node.text) > 0:
            return node.text
        else:
            return None


def parse_json(node):
    return _parse_recursive(node)
