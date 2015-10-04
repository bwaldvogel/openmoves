revision = '17'
down_revision = '16'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('sample', sa.Column('relative_performance_level', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('sample', 'relative_performance_level')
