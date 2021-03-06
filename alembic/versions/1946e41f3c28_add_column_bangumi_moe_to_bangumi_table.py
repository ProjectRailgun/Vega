"""add column bangumi_moe to bangumi table

Revision ID: 1946e41f3c28
Revises: f0fe71ca3d01
Create Date: 2017-04-09 21:58:17.434001

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# revision identifiers, used by Alembic.
from future import standard_library
standard_library.install_aliases()
from builtins import *
revision = '1946e41f3c28'
down_revision = 'f0fe71ca3d01'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bangumi', sa.Column('bangumi_moe', sa.TEXT(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bangumi', 'bangumi_moe')
    # ### end Alembic commands ###
