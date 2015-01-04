#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
import math
import gpxpy.gpx

def radianToDegree(value):
    return 180.0 / math.pi * value

def gpxExport(move):

    gpx = gpxpy.gpx.GPX()
    gpx.creator = "OpenMoves - http://www.openmoves.net/"

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Create points:
    samples = move.samples.order_by('time asc').all()
    gpsSamples = [sample for sample in samples if sample.sampleType and sample.sampleType.startswith('gps-')]

    for gpsSample in gpsSamples:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=radianToDegree(gpsSample.latitude),
                                                          longitude=radianToDegree(gpsSample.longitude),
                                                          elevation=gpsSample.gpsAltitude,
                                                          time=move.dateTime + gpsSample.time
                                                        ))

    # You can add routes and waypoints, too...
    return gpx.to_xml()
