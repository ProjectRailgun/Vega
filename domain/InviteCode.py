from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from domain.base import Base
from sqlalchemy import Column
from sqlalchemy.dialects import postgresql
from uuid import uuid4


class InviteCode(Base):
    __tablename__ = 'invite_code'

    code = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    used_by = Column(postgresql.UUID(as_uuid=True), nullable=True)
