revision = '18'
down_revision = '17'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('user_preference',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(65536), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('user_preference_user_id_key', 'user_preference', ['user_id', 'key'], unique=True)

def downgrade():
    op.drop_index('user_preference_user_id_key', table_name='user_preference')
    op.drop_table('user_preference')
