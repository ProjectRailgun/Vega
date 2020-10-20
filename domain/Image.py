from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from domain.base import Base
from sqlalchemy import Column, TEXT, String, Integer
from sqlalchemy.dialects import postgresql
from uuid import uuid4


class Image(Base):
    __tablename__ = 'image'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_path = Column(TEXT, nullable=False)
    dominant_color = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
