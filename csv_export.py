#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
from flask import flash
from filters import radian_to_degree, format_distance, format_speed, format_altitude, format_temparature, format_hr, \
    format_energyconsumption, format_date_time
from functools import partial


csv_export_unit = False


def addValue(row_array, value, formatter=None):
    if not value:
        row_array.append("")
    else:
        if formatter:
            row_array.append(str(formatter(value)))
        else:
            row_array.append(str(value))


def csv_export(move):
    samples = move.samples.order_by('time asc')

    if samples.count() == 0:
        flash("No samples found for CSV export", 'error')
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
        addValue(row, sample.altitude, formatter=partial(format_altitude, unit=csv_export_unit))

        addValue(row, sample.distance, formatter=partial(format_distance, unit=csv_export_unit))
        addValue(row, sample.speed, formatter=partial(format_speed, unit=csv_export_unit))
        addValue(row, sample.temperature, formatter=partial(format_temparature, unit=csv_export_unit))
        addValue(row, sample.hr, formatter=partial(format_hr, unit=csv_export_unit))
        addValue(row, sample.energy_consumption, formatter=partial(format_energyconsumption, unit=csv_export_unit))

        addValue(row, sample.gps_hdop)
        addValue(row, sample.vertical_speed, formatter=partial(format_speed, unit=csv_export_unit))
        addValue(row, sample.number_of_satellites)

        rows.append(";".join(row))

    # Finally merge all rows
    csv_data = "\r\n".join(rows)
    return csv_data
