revision = '13'
down_revision = '12'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('move_edit',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('date_time', sa.DateTime(), nullable=False),
                    sa.Column('move_id', sa.Integer(), nullable=False),
                    sa.Column('old_value', sa.String(), nullable=False),
                    sa.Column('new_value', sa.String(), nullable=False),
                    sa.ForeignKeyConstraint(['move_id'], [u'move.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('move_edit')
