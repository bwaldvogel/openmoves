revision = '14'
down_revision = '13'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import timedelta


def upgrade():
    changeRecoveryTime(old=timedelta(seconds=0), new=None)


def downgrade():
    changeRecoveryTime(old=None, new=timedelta(seconds=0))


def changeRecoveryTime(old, new):
    Base = declarative_base()
    Session = sessionmaker(bind=op.get_bind())

    class Move(Base):
        __tablename__ = 'move'
        id = sa.Column(sa.Integer, name="id", primary_key=True)
        recovery_time = sa.Column(sa.Interval, name='recovery_time')

    session = Session()
    session.query(Move).filter(Move.recovery_time == old).update({'recovery_time': new})
    session.commit()
