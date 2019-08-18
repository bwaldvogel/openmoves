#!/usr/bin/env python

import gpxpy.gpx
from flask import flash

from filters import radian_to_degree
from model import Sample


def gpx_export(move):

    gpx = gpxpy.gpx.GPX()
    gpx.creator = "OpenMoves - http://www.openmoves.net/"

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Create points:
    gps_samples = move.samples.filter(Sample.sample_type.like('gps-%')).order_by(Sample.time.asc())

    if gps_samples.count() == 0:
        flash("No GPS samples found for GPX export", 'error')
        return None

    for gps_sample in gps_samples:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=radian_to_degree(gps_sample.latitude),
                                                          longitude=radian_to_degree(gps_sample.longitude),
                                                          elevation=gps_sample.gps_altitude,
                                                          time=move.date_time + gps_sample.time,
                                                          position_dilution=gps_sample.gps_hdop))

    # You can add routes and waypoints, too...
    return gpx.to_xml()
