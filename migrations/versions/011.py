revision = '11'
down_revision = '10'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def upgrade():
    op.add_column('move', sa.Column('location_address', sa.String(), nullable=True))
    op.add_column('move', sa.Column('location_raw', sa.String(), nullable=True))
    op.add_column('move', sa.Column('gps_center_max_distance', sa.Float(), nullable=True))
    op.add_column('move', sa.Column('gps_center_latitude', sa.Float(), nullable=True))
    op.add_column('move', sa.Column('gps_center_longitude', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('move', 'gps_center_latitude')
    op.drop_column('move', 'gps_center_longitude')
    op.drop_column('move', 'gps_center_max_distance')
    op.drop_column('move', 'location_address')
    op.drop_column('move', 'location_raw')


