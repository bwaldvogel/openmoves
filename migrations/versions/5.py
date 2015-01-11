revision = '5'
down_revision = '4'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def upgrade():
    changeActivity(old='Outdoor swimmin', new='Outdoor swimming')


def downgrade():
    changeActivity(old='Outdoor swimming', new='Outdoor swimmin')


def changeActivity(old, new):
    Base = declarative_base()
    Session = sessionmaker(bind=op.get_bind())

    class Move(Base):
        __tablename__ = 'move'
        id = sa.Column(sa.Integer, name="id", primary_key=True)
        activity = sa.Column(sa.String, name='activity')

    session = Session()
    session.query(Move).filter(Move.activity == old).update({'activity': new})
    session.commit()
