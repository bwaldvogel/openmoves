revision = '22'
down_revision = '21'

from alembic import op


def upgrade():
    op.alter_column('move', 'device_id', nullable=True)


def downgrade():
    op.alter_column('move', 'device_id', nullable=False)
