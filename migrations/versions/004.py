revision = '4'
down_revision = '3'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func


def upgrade():
    op.add_column('move', sa.Column('temperature_avg', sa.Float(), nullable=True))
    calculateAverageTemperatures()


def downgrade():
    op.drop_column('move', 'temperature_avg')


def calculateAverageTemperatures():
    Base = declarative_base()
    Session = sessionmaker(bind=op.get_bind())

    class Sample(Base):
        __tablename__ = 'sample'
        id = sa.Column(sa.Integer, name="id", primary_key=True)
        moveId = sa.Column(sa.Integer, name="move_id", nullable=False)
        temperature = sa.Column(sa.Float, name='temperature')

    class Move(Base):
        __tablename__ = 'move'
        id = sa.Column(sa.Integer, name="id", primary_key=True)
        temperature_avg = sa.Column(sa.Float, name='temperature_avg')

    session = Session()
    averageTemperatures = dict(session.query(Sample.moveId, func.avg(Sample.temperature)).group_by(Sample.moveId).filter(Sample.temperature > 0).all())

    for move in session.query(Move):
        if move.id in averageTemperatures:
            move.temperature_avg = averageTemperatures[move.id]

    session.commit()
