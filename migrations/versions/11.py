revision = '11'
down_revision = '10'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geopy.geocoders import Nominatim
from geopy.distance import vincenty
import numpy as np
import math
import json


def radian_to_degree(value):
    return 180.0 / math.pi * value


def upgrade():
    op.add_column('move', sa.Column('location_address', sa.String(), nullable=True))
    op.add_column('move', sa.Column('location_raw', sa.String(), nullable=True))
    op.add_column('move', sa.Column('gps_center_max_distance', sa.Float(), nullable=True))
    op.add_column('move', sa.Column('gps_center_latitude', sa.Float(), nullable=True))
    op.add_column('move', sa.Column('gps_center_longitude', sa.Float(), nullable=True))

    postprocess_moves()


def downgrade():
    op.drop_column('move', 'gps_center_latitude')
    op.drop_column('move', 'gps_center_longitude')
    op.drop_column('move', 'gps_center_max_distance')
    op.drop_column('move', 'location_address')
    op.drop_column('move', 'location_raw')


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
    lon = math.atan2(y, x)
    hyp = np.sqrt(x * x + y * y)
    lat = math.atan2(z, hyp)

    center = (lat, lon)
    return center


def postprocess_moves():

    Base = declarative_base()
    Session = sessionmaker(bind=op.get_bind())

    class Move(Base):
        __tablename__ = 'move'
        id = sa.Column(sa.Integer, name="id", primary_key=True)
        activity = sa.Column(sa.String, name='activity')

        location_address = sa.Column(sa.String, name="location_address")
        location_raw = sa.Column(sa.String, name="location_raw")
        gps_center_max_distance = sa.Column(sa.Float, name="gps_center_max_distance")
        gps_center_latitude = sa.Column(sa.Float, name="gps_center_latitude")
        gps_center_longitude = sa.Column(sa.Float, name="gps_center_longitude")

    class Sample(Base):
        __tablename__ = 'sample'
        id = sa.Column(sa.Integer, name="id", primary_key=True)

        moveId = sa.Column(sa.Integer, sa.ForeignKey(Move.id), name="move_id", nullable=False)
        move = sa.orm.relationship(Move, backref=sa.orm.backref('samples', lazy='dynamic'))

        sample_type = sa.Column(sa.String, name='sample_type')

        longitude = sa.Column(sa.Float, name='longitude')
        latitude = sa.Column(sa.Float, name='latitude')

    session = Session()
    moves_count = session.query(Move).count()
    for idx, move in enumerate(session.query(Move)):

        print(u"processing move %d/%d" % (idx + 1, moves_count))

        gps_samples = [sample for sample in move.samples if sample.sample_type and sample.sample_type.startswith('gps-')]

        if len(gps_samples) > 0:
            print(u"  got %d GPS samples for move %d: %s" % (len(gps_samples), move.id, move.activity))

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
            location = geolocator.reverse("%f, %f" % (radian_to_degree(latitude), radian_to_degree(longitude)))
            move.location_address = location.address
            move.location_raw = json.dumps(location.raw)
        else:
            print(u"  got no GPS samples for move %d: %s" % (move.id, move.activity))
