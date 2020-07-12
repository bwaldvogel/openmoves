from datetime import datetime, timedelta

import numpy as np
import pytz
import stravalib
from sqlalchemy.sql import func

import gpx_import
from _import import postprocess_move
from filters import degree_to_radian, celcius_to_kelvin
from model import User, Device, Move, Sample, db

MAX_DATE_TIME_OFFSET = timedelta(hours=2, minutes=30)

SAMPLE_TYPE = 'gps-base'


def map_type(type):
    if type == 'Run':
        return 'Running'
    elif type == 'Swim':
        return 'Pool swimming'
    elif type == 'Ride':
        return 'Cycling'
    elif type == 'Hike':
        return 'Trekking'
    else:
        return type


def strava_import(current_user, activity_id):
    client = get_strava_client(current_user)
    activity = client.get_activity(activity_id=activity_id)
    stream_types = ['time', 'distance', 'latlng', 'temp', 'heartrate', 'velocity_smooth', 'altitude']
    streams = client.get_activity_streams(activity_id, types=stream_types)

    activity_string = map_type(activity.type)

    result = db.session.query(Move.activity_type).filter(Move.activity == activity_string).first()
    if result:
        activity_type, = result
    else:
        activity_type = None

    device = find_device(current_user)

    move = Move()
    move.user = current_user
    move.duration = activity.elapsed_time
    move.ascent = float(activity.total_elevation_gain)
    move.speed_avg = float(activity.average_speed)
    move.hr_avg = heart_rate(activity.average_heartrate)
    move.temperature_avg = celcius_to_kelvin(activity.average_temp)
    move.device = device
    move.date_time = activity.start_date_local
    move.activity = activity_string
    move.activity_type = activity_type
    move.distance = float(activity.distance)
    move.import_date_time = datetime.now()
    move.import_module = __name__
    move.strava_activity_id = activity_id
    move.public = False
    move.source = "Strava activity id=%d; external_id='%s'" % (activity_id, activity.external_id)

    if streams:
        lengths = set([len(streams[stream].data) for stream in streams])
        assert len(lengths) == 1
        length, = lengths
    else:
        length = 0

    move.speed_max = move.speed_avg

    all_samples = []
    for i in range(0, length):
        time = timedelta(seconds=streams['time'].data[i])

        if 'distance' in streams:
            distance = float(streams['distance'].data[i])
        else:
            distance = None

        if 'heartrate' in streams:
            hr = float(streams['heartrate'].data[i])
        else:
            hr = None

        if 'latlng' in streams:
            lat, lng = streams['latlng'].data[i]
        else:
            lat = None
            lng = None

        if 'altitude' in streams:
            altitude = float(streams['altitude'].data[i])
        else:
            altitude = None

        if 'velocity_smooth' in streams:
            speed = float(streams['velocity_smooth'].data[i])
        else:
            speed = None

        if 'temp' in streams:
            temperature = celcius_to_kelvin(streams['temp'].data[i])
        else:
            temperature = None

        sample = Sample()
        sample.sample_type = SAMPLE_TYPE
        sample.move = move
        sample.time = time
        sample.utc = (activity.start_date + time).replace(tzinfo=None)
        sample.distance = distance
        sample.latitude = degree_to_radian(lat)
        sample.longitude = degree_to_radian(lng)
        sample.hr = heart_rate(hr)
        sample.temperature = temperature
        sample.speed = speed
        sample.altitude = altitude
        move.speed_max = max(move.speed_max, speed)
        all_samples.append(sample)

    derive_move_infos_from_samples(move, all_samples)

    db.session.add(move)
    db.session.flush()
    postprocess_move(move)
    db.session.commit()
    return move


def find_device(current_user):
    device_ids = [device_id for device_id, in db.session.query(func.distinct(Move.device_id))
        .join(User)
        .join(Device)
        .filter(Device.name != gpx_import.GPX_DEVICE_NAME)
        .filter(Move.user == current_user).all()]

    if not device_ids:
        return None

    assert len(device_ids) == 1
    device_id = device_ids[0]
    device = db.session.query(Device).filter_by(id=device_id).one()
    return device


def get_strava_client(current_user):
    strava_access_token = current_user.get_strava_access_token()
    client = stravalib.client.Client(access_token=strava_access_token)
    return client


def derive_move_infos_from_samples(move, samples):
    if len(samples) <= 0:
        return

    move.log_item_count = len(samples)

    # Altitudes
    altitudes = np.asarray([sample.altitude for sample in samples if sample.altitude is not None], dtype=float)
    if len(altitudes) > 0:
        move.altitude_min = np.min(altitudes)
        move.altitude_max = np.max(altitudes)

        # Total ascent / descent
        move.ascent = 0
        move.ascent_time = timedelta(0)
        move.descent = 0
        move.descent_time = timedelta(0)

    previous_sample = None

    # Accumulate values from samples
    for sample in samples:
        # Skip calculation on first sample, sample without altitude info, pause event
        if previous_sample:
            # Calculate altitude and time sums
            if sample.altitude is not None and previous_sample.altitude is not None:
                altitude_diff = sample.altitude - previous_sample.altitude
                time_diff = sample.time - previous_sample.time
                if altitude_diff > 0:
                    move.ascent += altitude_diff
                    move.ascent_time += time_diff
                elif altitude_diff < 0:
                    move.descent += -altitude_diff
                    move.descent_time += time_diff

        # Store sample for next cycle
        previous_sample = sample

    # Temperature
    temperatures = np.asarray([sample.temperature for sample in samples if sample.temperature], dtype=float)
    if len(temperatures) > 0:
        move.temperature_min = np.min(temperatures)
        move.temperature_max = np.max(temperatures)

    # Heart rate
    hrs = np.asarray([sample.hr for sample in samples if sample.hr], dtype=float)
    if len(hrs) > 0:
        move.hr_min = np.min(hrs)
        move.hr_max = np.max(hrs)


def heart_rate(hr):
    if hr is None:
        return None
    return float(hr) / 60.0


def associate_activities(user, before=None, after=None):
    assert user.has_strava()
    moves_by_date_time = {}
    for id, date_time in db.session.query(Sample.move_id, func.min(Sample.utc)) \
            .join(Move) \
            .filter(Sample.utc != None) \
            .filter(Move.user == user) \
            .group_by(Sample.move_id):
        utc = date_time.replace(tzinfo=pytz.UTC)
        moves_by_date_time[utc] = id
    moves_by_strava_activity_id = {}
    for id, strava_activity_id in db.session.query(Move.id, Move.strava_activity_id) \
            .filter(Move.user == user) \
            .filter(Move.strava_activity_id != None):
        moves_by_strava_activity_id[strava_activity_id] = id
    new_strava_activities = []
    associated_strava_activities = []
    known_strava_activities = []
    client = get_strava_client(user)
    for activity in client.get_activities(before=before, after=after):
        move_id = None
        start_date = activity.start_date
        if activity.id in moves_by_strava_activity_id:
            move_id = moves_by_strava_activity_id[activity.id]
        elif start_date in moves_by_date_time:
            move_id = moves_by_date_time[start_date]
        else:
            for date_time in moves_by_date_time.keys():
                start_date_delta = abs(date_time - start_date)
                start_date_local_delta = abs(date_time - activity.start_date_local.replace(tzinfo=pytz.UTC))
                max_delta = timedelta(seconds=30)

                if start_date_delta <= max_delta or start_date_local_delta <= max_delta:
                    move_id = moves_by_date_time[date_time]
                    break

            if not move_id:
                potential_moves = []
                for date_time in moves_by_date_time.keys():
                    start_date_delta = abs(date_time - start_date)
                    if -MAX_DATE_TIME_OFFSET <= start_date_delta <= MAX_DATE_TIME_OFFSET:
                        potential_moves.append(moves_by_date_time[date_time])

                if len(potential_moves) == 1:
                    move_id = potential_moves[0]
                elif len(potential_moves) > 1:
                    # too many candidates found
                    pass

        if not move_id:
            new_strava_activities.append(activity)
        elif activity.id in moves_by_strava_activity_id:
            known_strava_activities.append(activity)
        else:
            move = Move.query.filter_by(id=move_id).one()
            move.strava_activity_id = activity.id
            db.session.commit()
            associated_strava_activities.append((activity, move))

    return associated_strava_activities, known_strava_activities, new_strava_activities
