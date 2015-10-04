revision = '9'
down_revision = '8'

from alembic import op

column = 'speed_max'

def upgrade():
    op.create_index("move_user_id_%s_idx" % column, 'move', ['user_id', column], unique=False)


def downgrade():
    op.drop_index("move_user_id_%s_idx" % column, table_name='move')
