#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
from flask import flash
from filters import radian_to_degree, format_distance, format_speed, format_altitude, format_temparature, format_hr, \
    format_energyconsumption, format_date_time_millis, format_date_time
from functools import partial


csvExportUnit = False

def addValue(rowArray, value, formatter=None):
    if not value:
        rowArray.append("")
    else:
        if formatter:
            rowArray.append(str(formatter(value)))
        else:
            rowArray.append(str(value))

def csv_export(move):
    samples = move.samples.order_by('time asc').all()

    if len(samples) == 0:
        flash("No samples found for GPX export", 'error')
        return None

    # Header
    header = ["Timestamp",
              "Duration",
              "Latitude [deg]",
              "Longitude [deg]",
              "Altitude [m]",

              "Distance [km]",
              "Speed [km/h]",
              "Temperature [°C]",
              "Heart rate [bpm]",
              "Energy consumption [kcal/min]",

              "HDOP",
              "Vertical speed [km/h]",
              "Number of satellites"
              ]
    rows = [";".join(header)]

    for sample in samples:
        row = []

        addValue(row, move.date_time + sample.time, formatter=format_date_time)
        addValue(row, sample.time)
        addValue(row, sample.latitude, formatter=radian_to_degree)
        addValue(row, sample.longitude, formatter=radian_to_degree)
        addValue(row, sample.altitude, formatter=partial(format_altitude, unit=csvExportUnit))

        addValue(row, sample.distance, formatter=partial(format_distance, unit=csvExportUnit))
        addValue(row, sample.speed, formatter=partial(format_speed, unit=csvExportUnit))
        addValue(row, sample.temperature, formatter=partial(format_temparature, unit=csvExportUnit))
        addValue(row, sample.hr, formatter=partial(format_hr, unit=csvExportUnit))
        addValue(row, sample.energy_consumption, formatter=partial(format_energyconsumption, unit=csvExportUnit))

        addValue(row, sample.gps_hdop)
        addValue(row, sample.vertical_speed, formatter=partial(format_speed, unit=csvExportUnit))
        addValue(row, sample.number_of_satellites)

        rows.append(";".join(row))

    # Finally merge all rows
    csvExport = "\r\n".join(rows)
    return csvExport
