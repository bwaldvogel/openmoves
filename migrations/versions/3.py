revision = '3'
down_revision = '2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.rename_table('logentry', 'move')
    op.alter_column('sample', 'log_entry_id', new_column_name='move_id', existing_type=sa.Integer())


def downgrade():
    op.rename_table('move', 'logentry')
    op.alter_column('sample', 'move_id', new_column_name='log_entry_id', existing_type=sa.Integer())
