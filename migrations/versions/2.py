revision = '2'
down_revision = '1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('device', 'name', existing_type=sa.VARCHAR(), nullable=True)


def downgrade():
    op.alter_column('device', 'name', existing_type=sa.VARCHAR(), nullable=False, server_default='')
