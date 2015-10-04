revision = '12'
down_revision = '11'

from alembic import op

column = 'location_address'

def upgrade():
    op.create_index("move_user_id_%s_idx" % column, 'move', ['user_id', column], unique=False)


def downgrade():
    op.drop_index("move_user_id_%s_idx" % column, table_name='move')
