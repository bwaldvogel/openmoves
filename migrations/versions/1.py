revision = '1'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('device',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('serial_number', sa.String(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('serial_number')
                    )

    op.create_table('user',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('username', sa.String(), nullable=False),
                    sa.Column('password', sa.String(), nullable=False),
                    sa.Column('active', sa.Boolean(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('username')
                    )

    op.create_table('logentry',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('device_id', sa.Integer(), nullable=False),
                    sa.Column('date_time', sa.DateTime(), nullable=False),
                    sa.Column('duration', sa.Interval(), nullable=True),
                    sa.Column('distance', sa.Integer(), nullable=True),
                    sa.Column('activity', sa.String(), nullable=True),
                    sa.Column('activity_type', sa.Integer(), nullable=True),
                    sa.Column('log_item_count', sa.Integer(), nullable=True),
                    sa.Column('ascent', sa.Integer(), nullable=True),
                    sa.Column('descent', sa.Integer(), nullable=True),
                    sa.Column('ascent_time', sa.Interval(), nullable=True),
                    sa.Column('descent_time', sa.Interval(), nullable=True),
                    sa.Column('recovery_time', sa.Interval(), nullable=True),
                    sa.Column('speed_avg', sa.Float(), nullable=True),
                    sa.Column('speed_max', sa.Float(), nullable=True),
                    sa.Column('speed_max_time', sa.Interval(), nullable=True),
                    sa.Column('hr_avg', sa.Float(), nullable=True),
                    sa.Column('hr_min', sa.Float(), nullable=True),
                    sa.Column('hr_max', sa.Float(), nullable=True),
                    sa.Column('hr_min_time', sa.Interval(), nullable=True),
                    sa.Column('hr_max_time', sa.Interval(), nullable=True),
                    sa.Column('peak_training_effect', sa.Float(), nullable=True),
                    sa.Column('energy', sa.Float(), nullable=True),
                    sa.Column('cadence_avg', sa.Float(), nullable=True),
                    sa.Column('cadence_max', sa.Float(), nullable=True),
                    sa.Column('cadence_max_time', sa.Interval(), nullable=True),
                    sa.Column('altitude_min', sa.Integer(), nullable=True),
                    sa.Column('altitude_max', sa.Integer(), nullable=True),
                    sa.Column('altitude_min_time', sa.Interval(), nullable=True),
                    sa.Column('altitude_max_time', sa.Interval(), nullable=True),
                    sa.Column('temperature_min', sa.Float(), nullable=True),
                    sa.Column('temperature_max', sa.Float(), nullable=True),
                    sa.Column('temperature_min_time', sa.Float(), nullable=True),
                    sa.Column('temperature_max_time', sa.Float(), nullable=True),
                    sa.Column('time_to_first_fix', sa.Integer(), nullable=True),
                    sa.Column('battery_charge_at_start', sa.Integer(), nullable=True),
                    sa.Column('battery_charge', sa.Integer(), nullable=True),
                    sa.Column('distance_before_calibration_change', sa.Integer(), nullable=True),
                    sa.Column('pool_length', sa.Integer(), nullable=True),
                    sa.Column('device_info_sw', sa.String(), nullable=True),
                    sa.Column('device_info_hw', sa.String(), nullable=True),
                    sa.Column('device_info_bsl', sa.String(), nullable=True),
                    sa.Column('device_info_sw_build_date_time', sa.DateTime(), nullable=True),
                    sa.Column('source', sa.String(), nullable=True),

                    sa.ForeignKeyConstraint(['device_id'], [u'device.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], [u'user.id'], ),

                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_index('logentry_user_id_date_time_idx', 'logentry', ['user_id', 'date_time'], unique=False)

    op.create_table('sample',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('log_entry_id', sa.Integer(), nullable=False),
                    sa.Column('sample_type', sa.String(), nullable=True),
                    sa.Column('time', sa.Interval(), nullable=True),
                    sa.Column('utc', sa.DateTime(), nullable=True),
                    sa.Column('distance', sa.Float(), nullable=True),
                    sa.Column('speed', sa.Float(), nullable=True),
                    sa.Column('temperature', sa.Float(), nullable=True),
                    sa.Column('hr', sa.Float(), nullable=True),
                    sa.Column('energy_consumption', sa.Float(), nullable=True),
                    sa.Column('vertical_speed', sa.Float(), nullable=True),
                    sa.Column('sea_level_pressure', sa.Float(), nullable=True),
                    sa.Column('gps_altitude', sa.Float(), nullable=True),
                    sa.Column('gps_heading', sa.Float(), nullable=True),
                    sa.Column('gps_speed', sa.Float(), nullable=True),
                    sa.Column('gps_hdop', sa.Float(), nullable=True),
                    sa.Column('number_of_satellites', sa.Integer(), nullable=True),
                    sa.Column('latitude', sa.Float(), nullable=True),
                    sa.Column('longitude', sa.Float(), nullable=True),
                    sa.Column('altitude', sa.Integer(), nullable=True),
                    sa.Column('ehpe', sa.Float(), nullable=True),
                    sa.Column('cadence', sa.Float(), nullable=True),
                    sa.Column('nav_type', sa.Integer(), nullable=True),
                    sa.Column('nav_valid', sa.String(), nullable=True),
                    sa.Column('nav_type_explanation', sa.String(), nullable=True),
                    sa.Column('events', sa.String(), nullable=True),
                    sa.Column('satellites', sa.String(), nullable=True),
                    sa.Column('apps_data', sa.String(), nullable=True),

                    sa.ForeignKeyConstraint(['log_entry_id'], [u'logentry.id'], ),

                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_index('sample_log_entry_id_time_idx', 'sample', ['log_entry_id', 'time'], unique=False)


def downgrade():
    op.drop_table('sample')
    op.drop_table('logentry')
    op.drop_table('user')
    op.drop_table('device')
