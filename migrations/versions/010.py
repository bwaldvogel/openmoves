revision = '10'
down_revision = '9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('move', sa.Column('import_date_time', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('move', 'import_date_time')
