revision = '23'
down_revision = '22'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('move', 'strava_activity_id', type_=sa.BigInteger(), existing_type=sa.Integer())


def downgrade():
    op.alter_column('move', 'strava_activity_id', type_=sa.BigInteger(), existing_type=sa.Integer())
