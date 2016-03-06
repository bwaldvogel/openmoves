revision = '19'
down_revision = '18'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def upgrade():
    op.add_column('move', sa.Column('public', sa.Boolean(), nullable=True))

    initialize_move_public()

    op.alter_column('move', 'public', existing_type=sa.Boolean(), nullable=False)


def downgrade():
    op.drop_column('move', 'public')


def initialize_move_public():
    Base = declarative_base()
    Session = sessionmaker(bind=op.get_bind())

    class Move(Base):
        __tablename__ = 'move'
        id = sa.Column(sa.Integer, name='id', primary_key=True)
        public = sa.Column(sa.Boolean, name='public')

    session = Session()
    session.query(Move).update({'public': False})
    session.commit()
