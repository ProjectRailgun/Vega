"""add column on bangumi table eps_no_offset

Revision ID: f435b0c46cc2
Revises: 1c38ccd23bb2
Create Date: 2016-10-16 19:29:33.061671

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# revision identifiers, used by Alembic.
from future import standard_library
standard_library.install_aliases()
from builtins import *
revision = 'f435b0c46cc2'
down_revision = '1c38ccd23bb2'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bangumi', sa.Column('eps_no_offset', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bangumi', 'eps_no_offset')
    ### end Alembic commands ###
