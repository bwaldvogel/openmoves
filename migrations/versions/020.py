revision = '20'
down_revision = '19'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('move', 'gps_center_max_distance')
    op.drop_column('move', 'gps_center_latitude')
    op.drop_column('move', 'gps_center_longitude')

def downgrade():
    op.add_column('move', sa.Column('gps_center_max_distance', sa.Float(), nullable=True))
    op.add_column('move', sa.Column('gps_center_latitude', sa.Float(), nullable=True))
    op.add_column('move', sa.Column('gps_center_longitude', sa.Float(), nullable=True))
