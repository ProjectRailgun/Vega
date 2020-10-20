from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from .base import Base
from sqlalchemy import TEXT, Column, DateTime, LargeBinary
from sqlalchemy.dialects import postgresql
from uuid import uuid4

class ServerSession(Base):
    __tablename__ = 'server_session'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(TEXT, unique=True)
    data = Column(LargeBinary)
    expiry = Column(DateTime)
