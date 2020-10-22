"""add image table

Revision ID: 875ae1099af9
Revises: 3ffc63f8e34f
Create Date: 2017-08-28 16:16:45.138681

"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

# revision identifiers, used by Alembic.
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import *
revision = '875ae1099af9'
down_revision = '3ffc63f8e34f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from PIL import Image
from urllib.parse import urlparse
import yaml
import os
from uuid import uuid4
from utils.image import get_dominant_color


def get_base_path():
    fr = open('./config/config.yml', 'r')
    config = yaml.safe_load(fr)
    return config['download']['location']


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('image',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('file_path', sa.TEXT(), nullable=False),
                    sa.Column('dominant_color', sa.String(), nullable=True),
                    sa.Column('width', sa.Integer(), nullable=True),
                    sa.Column('height', sa.Integer(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.add_column(u'bangumi', sa.Column('cover_image_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(u'episodes', sa.Column('thumbnail_image_id', postgresql.UUID(as_uuid=True), nullable=True))
    # ### end Alembic commands ###

    # import data into image table.
    connection = op.get_bind()
    result = connection.execute(sa.text(
        'SELECT bangumi.id, bangumi.image, bangumi.cover_color FROM bangumi WHERE bangumi.image NOTNULL'))
    base_path = get_base_path()
    for row in result:
        bangumi_id = row[0]
        bangumi_image = row[1]
        dominant_color = row[2]
        path = urlparse(bangumi_image).path
        extname = os.path.splitext(path)[1]
        image_path = os.path.join(str(bangumi_id), 'cover' + extname)
        if not os.path.exists(os.path.join(base_path, image_path)):
            print('cover not found for {0}'.format(bangumi_id))
            continue
        try:
            image_id = uuid4()
            connection.execute(sa.text(
                "INSERT INTO image (id, file_path, dominant_color) VALUES ('{0}', '{1}', '{2}')".format(
                    image_id, image_path, dominant_color)))
            connection.execute(sa.text(
                "UPDATE bangumi SET cover_image_id = '{0}' WHERE id = '{1}'".format(image_id, bangumi_id)))
        except Exception as error:
            print(error)

        # query episodes
        episode_result = connection.execute(sa.text(
            "SELECT e.id, e.episode_no, e.thumbnail_color FROM episodes e WHERE e.status = 2 AND e.bangumi_id = '{0}'".format(
                bangumi_id)))

        for eps in episode_result:
            episode_id = eps[0]
            episode_no = eps[1]
            episode_thumbnail_color = eps[2]
            thumbnail_path = os.path.join(str(bangumi_id), 'thumbnails', episode_no + '.png')
            if not os.path.exists(os.path.join(base_path, thumbnail_path)):
                print('thumbnail not found for {0}'.format(episode_id))
                continue
            try:
                image_id = uuid4()
                connection.execute(sa.text(
                    "INSERT INTO image (id, file_path, dominant_color) VALUES ('{0}', '{1}', '{2}')".format(
                        image_id, thumbnail_path, episode_thumbnail_color)))
                connection.execute(sa.text(
                    "UPDATE episodes SET thumbnail_image_id = '{0}' WHERE id = '{1}'".format(image_id, episode_id)))
            except Exception as error:
                print(error)
    print('image table import completed. Start reading image dimension and fix color')

    image_result = connection.execute(sa.text('SELECT image.id, image.file_path, image.dominant_color FROM image'))
    for image in image_result:
        image_id = image[0]
        image_file_path = image[1]
        image_dominant_color = image[2]
        try:
            im = Image.open(os.path.join(base_path, image_file_path))
            (width, height) = im.size
            if image_dominant_color is None:
                image_dominant_color = get_dominant_color(os.path.join(base_path, image_file_path), 5)
            connection.execute(sa.text(
                "UPDATE image SET width = '{0}', height = '{1}', dominant_color = '{2}' WHERE id = '{3}'".format(
                    width, height, image_dominant_color, image_id)))
        except Exception as error:
            print(error)
    print('All done')


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'episodes', 'thumbnail_image_id')
    op.drop_column(u'bangumi', 'cover_image_id')
    op.drop_table('image')
    # ### end Alembic commands ###
