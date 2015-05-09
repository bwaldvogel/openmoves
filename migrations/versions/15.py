revision = '15'
down_revision = '14'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('move', 'battery_charge_at_start', type_=sa.Float(), existing_type=sa.Integer())
    op.alter_column('move', 'battery_charge', type_=sa.Float(), existing_type=sa.Integer())


def downgrade():
    op.alter_column('move', 'battery_charge_at_start', type_=sa.Integer(), existing_type=sa.Float())
    op.alter_column('move', 'battery_charge', type_=sa.Integer(), existing_type=sa.Float())
