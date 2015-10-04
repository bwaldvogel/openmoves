revision = '6'
down_revision = '5'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json


def upgrade():
    op.add_column('move', sa.Column('stroke_count', sa.Float(), nullable=True))
    changeActivity(old='Outdoor swimmin', new='Outdoor swimming')


def downgrade():
    op.drop_column('move', 'stroke_count')


def changeActivity(old, new):
    Base = declarative_base()
    Session = sessionmaker(bind=op.get_bind())

    class Move(Base):
        __tablename__ = 'move'
        id = sa.Column(sa.Integer, name="id", primary_key=True)
        activity = sa.Column(sa.String, name="activity")
        strokeCount = sa.Column(sa.Integer, name='stroke_count')

    class Sample(Base):
        __tablename__ = 'sample'
        id = sa.Column(sa.Integer, name="id", primary_key=True)

        moveId = sa.Column(sa.Integer, sa.ForeignKey(Move.id), name="move_id", nullable=False)
        move = sa.orm.relationship(Move, backref=sa.orm.backref('samples', lazy='dynamic'))

        events = sa.Column(sa.String, name='events')

    session = Session()
    for move in session.query(Move):
        strokeCount = 0
        for eventData, in session.query(Sample.events).filter(Sample.move == move, Sample.events != None):
            events = json.loads(eventData)
            if 'swimming' in events and events['swimming']['type'] == 'Stroke':
                strokeCount += 1

        if 'swimming' in move.activity:
            assert strokeCount > 0

        if strokeCount > 0:
            move.strokeCount = strokeCount

    session.commit()
