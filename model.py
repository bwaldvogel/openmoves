# vim: set fileencoding=utf-8 :
# written by Benedikt Waldvogel

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TypeDecorator
import json

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
    id = db.Column(db.Integer, name="id", primary_key=True)
    name = db.Column(db.String, name="name", nullable=True)
    serialNumber = db.Column(db.String, name="serial_number", unique=True, nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, name="id", primary_key=True)
    username = db.Column(db.String, name="username", unique=True, nullable=False)
    password = db.Column(db.String, name="password", nullable=False)
    active = db.Column(db.Boolean, name="active", nullable=False)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username


class LogEntry(db.Model):
    __tablename__ = 'logentry'
    id = db.Column(db.Integer, name="id", primary_key=True)

    userId = db.Column(db.Integer, db.ForeignKey(User.id), name="user_id", nullable=False)
    user = db.relationship(User, backref=db.backref('entries', lazy='dynamic'))

    deviceId = db.Column(db.Integer, db.ForeignKey(Device.id), name="device_id", nullable=False)
    device = db.relationship(Device, backref=db.backref('devices', lazy='dynamic'))

    dateTime = db.Column(db.DateTime, name="date_time", nullable=False)
    duration = db.Column(db.Interval, name="duration")
    distance = db.Column(db.Integer, name="distance")
    activity = db.Column(db.String, name="activity")
    activityType = db.Column(db.Integer, name="activity_type")
    logItemCount = db.Column(db.Integer, name="log_item_count")

    ascent = db.Column(db.Integer, name="ascent", nullable=True)
    descent = db.Column(db.Integer, name="descent", nullable=True)
    ascentTime = db.Column(db.Interval, name="ascent_time")
    descentTime = db.Column(db.Interval, name="descent_time")

    recoveryTime = db.Column(db.Interval, name="recovery_time")

    speedAvg = db.Column(db.Float, name="speed_avg")
    speedMax = db.Column(db.Float, name="speed_max")
    speedMaxTime = db.Column(db.Interval, name="speed_max_time")

    hrAvg = db.Column(db.Float, name="hr_avg")
    hrMin = db.Column(db.Float, name="hr_min")
    hrMax = db.Column(db.Float, name="hr_max")
    hrMinTime = db.Column(db.Interval, name="hr_min_time")
    hrMaxTime = db.Column(db.Interval, name="hr_max_time")

    peakTrainingEffect = db.Column(db.Float, name="peak_training_effect")
    energy = db.Column(db.Float, name="energy")

    cadenceAvg = db.Column(db.Float, name="cadence_avg")
    cadenceMax = db.Column(db.Float, name="cadence_max")
    cadenceMaxTime = db.Column(db.Interval, name="cadence_max_time")

    altitudeMin = db.Column(db.Integer, name="altitude_min")
    altitudeMax = db.Column(db.Integer, name="altitude_max")
    altitudeMinTime = db.Column(db.Interval, name="altitude_min_time")
    altitudeMaxTime = db.Column(db.Interval, name="altitude_max_time")

    temperatureMin = db.Column(db.Float, name="temperature_min")
    temperatureMax = db.Column(db.Float, name="temperature_max")
    temperatureMinTime = db.Column(db.Float, name="temperature_min_time")
    temperatureMaxTime = db.Column(db.Float, name="temperature_max_time")

    timeToFirstFix = db.Column(db.Integer, name="time_to_first_fix")

    batteryChargeAtStart = db.Column(db.Integer, name="battery_charge_at_start")
    batteryCharge = db.Column(db.Integer, name="battery_charge")

    distanceBeforeCalibrationChange = db.Column(db.Integer, name="distance_before_calibration_change")

    poolLength = db.Column(db.Integer, name="pool_length")

    deviceInfoSW = db.Column(db.String, name="device_info_sw")
    deviceInfoHW = db.Column(db.String, name="device_info_hw")
    deviceInfoBSL = db.Column(db.String, name="device_info_bsl")
    deviceInfoSWBuildDateTime = db.Column(db.DateTime, name="device_info_sw_build_date_time")

    source = db.Column(db.String, name="source")


class Sample(db.Model):
    id = db.Column(db.Integer, name="id", primary_key=True)

    logEntryId = db.Column(db.Integer, db.ForeignKey(LogEntry.id), name="log_entry_id", nullable=False)
    logEntry = db.relationship(LogEntry, backref=db.backref('samples', lazy='dynamic'))

    sampleType = db.Column(db.String, name='sample_type')
    time = db.Column(db.Interval, name='time')
    utc = db.Column(db.DateTime, name='utc')

    distance = db.Column(db.Float, name='distance')
    speed = db.Column(db.Float, name='speed')
    temperature = db.Column(db.Float, name='temperature')

    hr = db.Column(db.Float, name='hr')
    energyConsumption = db.Column(db.Float, name='energy_consumption')

    verticalSpeed = db.Column(db.Float, name='vertical_speed')
    seaLevelPressure = db.Column(db.Float, name='sea_level_pressure')

    gpsAltitude = db.Column(db.Float, name='gps_altitude')
    gpsHeading = db.Column(db.Float, name='gps_heading')
    gpsSpeed = db.Column(db.Float, name='gps_speed')
    gpsHDOP = db.Column(db.Float, name='gps_hdop')

    numberOfSatellites = db.Column(db.Integer, name='number_of_satellites')

    latitude = db.Column(db.Float, name='latitude')
    longitude = db.Column(db.Float, name='longitude')

    altitude = db.Column(db.Integer, name='altitude')

    ehpe = db.Column(db.Float, name='ehpe')

    cadence = db.Column(db.Float, name='cadence')

    navType = db.Column(db.Integer, name='nav_type')
    navValid = db.Column(db.String, name='nav_valid')
    navTypeExplanation = db.Column(db.String, name='nav_type_explanation')

    events = db.Column(JsonEncodedDict(4096), name='events')
    satellites = db.Column(JsonEncodedDict(4096), name='satellites')
    appsData = db.Column(JsonEncodedDict(4096), name='apps_data')
