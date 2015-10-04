revision = '7'
down_revision = '6'

from alembic import op


index_columns = ('activity', 'duration', 'distance', 'speed_avg', 'temperature_avg', 'ascent', 'descent', 'stroke_count', 'pool_length')


def upgrade():

    op.drop_index('logentry_user_id_date_time_idx', table_name='move')
    op.create_index('move_user_id_date_time_idx', 'move', ['user_id', 'date_time'], unique=True)

    for column in index_columns:
        op.create_index("move_user_id_%s_idx" % column, 'move', ['user_id', column], unique=False)


def downgrade():

    op.drop_index('move_user_id_date_time_idx', table_name='move')
    op.create_index('logentry_user_id_date_time_idx', 'move', ['user_id', 'date_time'], unique=False)

    for column in index_columns:
        op.drop_index("move_user_id_%s_idx" % column, table_name='move')
