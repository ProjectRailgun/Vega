from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from domain.base import Base
from sqlalchemy import Column, TEXT, Integer, TIMESTAMP
from sqlalchemy.dialects import postgresql
from uuid import uuid4


class Announce(Base):
    __tablename__ = 'announce'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    content = Column(TEXT, nullable=True)
    image_url = Column(TEXT, nullable=True)
    position = Column(Integer, nullable=False)
    sort_order = Column(Integer, nullable=True)
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)

    # some reserved position
    POSITION_BANNER = 1
    POSITION_BANGUMI = 2
