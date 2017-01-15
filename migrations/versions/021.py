revision = '21'
down_revision = '20'

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('move', sa.Column('strava_activity_id', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('move', 'strava_activity_id')
