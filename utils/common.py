from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import *
from builtins import object
import yaml
import os
import errno
from urllib.parse import urlparse
from datetime import datetime
import logging
from domain.Image import Image

from utils.db import row2dict

logger = logging.getLogger(__name__)


epoch = datetime.utcfromtimestamp(0)


class CommonUtils(object):

    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = yaml.safe_load(fr)
        self.base_path = config['download']['location']
        self.image_domain = config['domain']['image']
        self.video_domain = config['domain']['video']
        try:
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)
                print('create base dir %s successfully' % self.base_path)
        except OSError as exception:
            if exception.errno == errno.EACCES:
                # permission denied
                raise exception
            else:
                print(exception)

    def generate_thumbnail_link(self, episode, bangumi):
        thumbnail_url = '/image/{0}/thumbnails/{1}.png'.format(str(bangumi.id), str(episode.episode_no))
        if self.image_domain is not None:
            thumbnail_url = self.image_domain + thumbnail_url
        return thumbnail_url

    def generate_cover_link(self, bangumi):
        path = urlparse(bangumi.image).path
        extname = os.path.splitext(path)[1]
        cover_url = '/image/{0}/cover{1}'.format(str(bangumi.id), extname)
        if self.image_domain is not None:
            cover_url = self.image_domain + cover_url
        return cover_url

    def generate_video_link(self, bangumi_id, path):
        video_link = '/video/{0}/{1}'.format(bangumi_id, path)
        if self.video_domain is not None:
            video_link = self.video_domain + video_link
        return video_link

    def convert_image_dict(self, image_dict):
        new_dict = {
            'url': '/image/{0}'.format(image_dict['file_path']),
            'dominant_color': image_dict.get('dominant_color'),
            'width': image_dict.get('width'),
            'height': image_dict.get('height')
        }
        if self.image_domain is not None:
            new_dict['url'] = self.image_domain + new_dict['url']
        return new_dict

    def process_bangumi_dict(self, bangumi, bangumi_dict):
        if bangumi.cover_image is not None:
            bangumi_dict['cover_image'] = self.convert_image_dict(row2dict(bangumi.cover_image, Image))
        bangumi_dict.pop('cover_image_id', None)

    def process_episode_dict(self, episode, episode_dict):
        if episode.thumbnail_image is not None:
            episode_dict['thumbnail_image'] = self.convert_image_dict(row2dict(episode.thumbnail_image, Image))
        episode_dict.pop('thumbnail_image_id', None)

    def empty_to_none(self, dict, attr_name):
        return dict.get(attr_name, None) if dict.get(attr_name, None) else None


utils = CommonUtils()
