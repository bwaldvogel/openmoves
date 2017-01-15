# vim: set fileencoding=utf-8 :
# written by Benedikt Waldvogel

import json

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.types import TypeDecorator

db = SQLAlchemy()


class JsonEncodedDict(TypeDecorator):
    impl = db.String

    def process_bind_param(self, value, dialect):
        if value:
            assert isinstance(value, dict)
            return json.dumps(value)
        else:
            return value

    def process_result_value(self, value, dialect):
        if value and not isinstance(value, dict):
            return json.loads(value)
        else:
            return value


class Device(db.Model):
    __tablename__ = 'device'
    id = db.Column(db.Integer, name='id', primary_key=True)
    name = db.Column(db.String, name='name', nullable=True)
    serial_number = db.Column(db.String, name='serial_number', unique=True, nullable=False)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, name='id', primary_key=True)
    username = db.Column(db.String, name='username', unique=True, nullable=False)
    password = db.Column(db.String, name='password', nullable=False)
    active = db.Column(db.Boolean, name='active', nullable=False)

    preferences = db.relationship('UserPreference', collection_class=attribute_mapped_collection('key'), cascade="all, delete-orphan")

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def has_strava(self):
        return 'strava' in self.preferences

    def get_strava_access_token(self):
        assert self.has_strava()
        return self.preferences['strava'].value['access_token']

    def get_id(self):
        return self.username


class UserPreference(db.Model):
    __tablename__ = 'user_preference'
    id = db.Column(db.Integer, name='id', primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id), name='user_id', nullable=False)

    key = db.Column(db.String, name='key', nullable=False)
    value = db.Column(JsonEncodedDict(65536), name='value', nullable=True)

    def __init__(self, key, value):
        self.key = key
        self.value = value


class Move(db.Model):
    __tablename__ = 'move'
    id = db.Column(db.Integer, name='id', primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id), name='user_id', nullable=False)
    user = db.relationship(User, backref=db.backref('moves', lazy='dynamic'))

    public = db.Column(db.Boolean, name='public', nullable=False)

    device_id = db.Column(db.Integer, db.ForeignKey(Device.id), name='device_id', nullable=False)
    device = db.relationship(Device, backref=db.backref('devices', lazy='dynamic'))

    date_time = db.Column(db.DateTime, name='date_time', nullable=False)
    duration = db.Column(db.Interval, name='duration')
    distance = db.Column(db.Integer, name='distance')
    activity = db.Column(db.String, name='activity')
    activity_type = db.Column(db.Integer, name='activity_type')
    log_item_count = db.Column(db.Integer, name='log_item_count')
    stroke_count = db.Column(db.Integer, name='stroke_count')

    ascent = db.Column(db.Integer, name='ascent', nullable=True)
    descent = db.Column(db.Integer, name='descent', nullable=True)
    ascent_time = db.Column(db.Interval, name='ascent_time')
    descent_time = db.Column(db.Interval, name='descent_time')

    recovery_time = db.Column(db.Interval, name='recovery_time')

    speed_avg = db.Column(db.Float, name='speed_avg')
    speed_max = db.Column(db.Float, name='speed_max')
    speed_max_time = db.Column(db.Interval, name='speed_max_time')

    hr_avg = db.Column(db.Float, name='hr_avg')
    hr_min = db.Column(db.Float, name='hr_min')
    hr_max = db.Column(db.Float, name='hr_max')
    hr_min_time = db.Column(db.Interval, name='hr_min_time')
    hr_max_time = db.Column(db.Interval, name='hr_max_time')

    peak_training_effect = db.Column(db.Float, name='peak_training_effect')
    energy = db.Column(db.Float, name='energy')

    cadence_avg = db.Column(db.Float, name='cadence_avg')
    cadence_max = db.Column(db.Float, name='cadence_max')
    cadence_max_time = db.Column(db.Interval, name='cadence_max_time')

    altitude_min = db.Column(db.Integer, name='altitude_min')
    altitude_max = db.Column(db.Integer, name='altitude_max')
    altitude_min_time = db.Column(db.Interval, name='altitude_min_time')
    altitude_max_time = db.Column(db.Interval, name='altitude_max_time')

    temperature_min = db.Column(db.Float, name='temperature_min')
    temperature_max = db.Column(db.Float, name='temperature_max')
    temperature_min_time = db.Column(db.Float, name='temperature_min_time')
    temperature_max_time = db.Column(db.Float, name='temperature_max_time')

    temperature_avg = db.Column(db.Float, name='temperature_avg')

    time_to_first_fix = db.Column(db.Integer, name='time_to_first_fix')

    battery_charge_at_start = db.Column(db.Float, name='battery_charge_at_start')
    battery_charge = db.Column(db.Float, name='battery_charge')

    distance_before_calibration_change = db.Column(db.Integer, name='distance_before_calibration_change')

    pool_length = db.Column(db.Integer, name='pool_length')

    device_info_sw = db.Column(db.String, name='device_info_sw')
    device_info_hw = db.Column(db.String, name='device_info_hw')
    device_info_bsl = db.Column(db.String, name='device_info_bsl')
    device_info_sw_build_date_time = db.Column(db.DateTime, name='device_info_sw_build_date_time')

    source = db.Column(db.String, name='source')
    import_date_time = db.Column(db.DateTime, name='import_date_time', nullable=False)
    import_module = db.Column(db.String, name='import_module', nullable=False)

    location_address = db.Column('location_address', db.String, nullable=True)
    location_raw = db.Column('location_raw', JsonEncodedDict(4096), nullable=True)

    strava_activity_id = db.Column('strava_activity_id', db.Integer, nullable=True)


class Sample(db.Model):
    __tablename__ = 'sample'
    id = db.Column(db.Integer, name='id', primary_key=True)

    move_id = db.Column(db.Integer, db.ForeignKey(Move.id), name='move_id', nullable=False)
    move = db.relationship(Move, backref=db.backref('samples', lazy='dynamic'))

    sample_type = db.Column(db.String, name='sample_type')
    time = db.Column(db.Interval, name='time')
    utc = db.Column(db.DateTime, name='utc')

    distance = db.Column(db.Float, name='distance')
    speed = db.Column(db.Float, name='speed')
    temperature = db.Column(db.Float, name='temperature')

    hr = db.Column(db.Float, name='hr')
    energy_consumption = db.Column(db.Float, name='energy_consumption')
    relative_performance_level = db.Column(db.Float, name='relative_performance_level')

    vertical_speed = db.Column(db.Float, name='vertical_speed')
    sea_level_pressure = db.Column(db.Float, name='sea_level_pressure')

    gps_altitude = db.Column(db.Float, name='gps_altitude')
    gps_heading = db.Column(db.Float, name='gps_heading')
    gps_speed = db.Column(db.Float, name='gps_speed')
    gps_hdop = db.Column(db.Float, name='gps_hdop')

    number_of_satellites = db.Column(db.Integer, name='number_of_satellites')

    latitude = db.Column(db.Float, name='latitude')
    longitude = db.Column(db.Float, name='longitude')

    altitude = db.Column(db.Integer, name='altitude')

    ehpe = db.Column(db.Float, name='ehpe')  # Estimated Horizontal Position Error

    cadence = db.Column(db.Float, name='cadence')

    nav_type = db.Column(db.Integer, name='nav_type')
    nav_valid = db.Column(db.String, name='nav_valid')
    nav_type_explanation = db.Column(db.String, name='nav_type_explanation')

    events = db.Column(JsonEncodedDict(4096), name='events')
    satellites = db.Column(JsonEncodedDict(4096), name='satellites')
    apps_data = db.Column(JsonEncodedDict(4096), name='apps_data')


class MoveEdit(db.Model):
    __tablename__ = 'move_edit'
    id = db.Column(db.Integer, name='id', primary_key=True)

    date_time = db.Column(db.DateTime, name='date_time', nullable=False)

    move_id = db.Column(db.Integer, db.ForeignKey(Move.id), name='move_id', nullable=False)
    move = db.relationship(Move, backref=db.backref('edits', lazy='dynamic'))

    old_value = db.Column(JsonEncodedDict(4096), name='old_value')
    new_value = db.Column(JsonEncodedDict(4096), name='new_value')


class AlembicVersion(db.Model):
    __tablename__ = 'alembic_version'
    version_num = db.Column(db.String, name='version_num', primary_key=True)
