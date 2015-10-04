revision = '8'
down_revision = '7'

from alembic import op

column = 'hr_avg'

def upgrade():
    op.create_index("move_user_id_%s_idx" % column, 'move', ['user_id', column], unique=False)


def downgrade():
    op.drop_index("move_user_id_%s_idx" % column, table_name='move')
