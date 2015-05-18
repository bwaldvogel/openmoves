revision = '16'
down_revision = '15'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import re


def upgrade():
    op.add_column('move', sa.Column('import_module', sa.String(), nullable=True))

    postprocess_moves()

    op.alter_column('move', 'import_module', existing_type=sa.String(), nullable=False)


def downgrade():
    op.drop_column('move', 'import_module')


def postprocess_moves():

    Base = declarative_base()
    Session = sessionmaker(bind=op.get_bind())

    class Move(Base):
        __tablename__ = 'move'
        id = sa.Column(sa.Integer, name="id", primary_key=True)

        source = sa.Column(sa.String, name="source")
        import_date_time = sa.Column(sa.DateTime, name="import_date_time")
        import_module = sa.Column(sa.DateTime, name="import_module")

    session = Session()
    for move in session.query(Move):
        filename = move.source
        if re.match(r'log-.+\.xml(\.gz)?', filename):
            move.import_module = 'old_xml_import'
        elif re.match(r'.+\.sml(\.gz)?', filename):
            move.import_module = 'sml_import'
        elif re.match(r'.+\.gpx(\.gz)?', filename):
            move.import_module = 'gpx_import'
        else:
            raise ValueError("unknown source: %s" % move.source)

        session.commit()
