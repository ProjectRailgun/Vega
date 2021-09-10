from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from feed_scanner.AbstractScanner import AbstractScanner
from utils.exceptions import SchedulerError
import json
import socket
import requests
import re

import logging

logger = logging.getLogger(__name__)


class UNIVERSAL(AbstractScanner):

    def __init__(self, bangumi, episode_list, mode):
        super(self.__class__, self).__init__(bangumi, episode_list)
        self.mode = mode
        self.feed_url = self.universal[mode]
        universal_list = json.loads(self.bangumi.universal)
        for res in universal_list:
            if res['mode'] == mode:
                self.keyword = res['keyword']
                break

    def parse_feed(self):
        logger.debug('start scan %s (%s)', self.bangumi.name, self.bangumi.id)
        eps_no_list = [eps.episode_no for eps in self.episode_list]

        timeout = socket.getdefaulttimeout()
        # set timeout is provided
        if self.timeout is not None:
            timeout = self.timeout

        r = requests.get(self.feed_url, params={'keyword': self.keyword}, timeout=timeout)

        if r.status_code > 399:
            raise SchedulerError('Network Error %d'.format(r.status_code))

        item_array = r.json()

        result_list = []

        for item in item_array:
            eps_list = dict()
            for media_file in item['files']:
                logger.error(media_file)
                if media_file['ext'] is not None and media_file['ext'].lower() not in ('.mp4', ',mkv'):
                    continue
                eps_no = self.parse_episode_number(media_file['name'])
                if len(item_array) == 1 and eps_no == -1:
                    eps_no = 1
                file_size = self.parse_size(media_file['size'])
                if eps_no in eps_no_list:
                    if eps_no not in eps_list:
                        eps_list[eps_no] = {
                            'file_path': media_file['path'],
                            'file_name': media_file['name'],
                            'file_size': file_size
                        }
                    else:
                        if file_size > eps_list[eps_no]['file_size']:
                            eps_list[eps_no] = {
                                'file_path': media_file['path'],
                                'file_name': media_file['name'],
                                'file_size': file_size
                            }
            if len(eps_list) == 0:
                continue
            for eps_no, eps_data in eps_list.items():
                if self.mode == 'nyaa' or self.mode == 'dmhy':
                    download_uri = item['magnet_uri']
                else:
                    download_uri = item['torrent_url']
                result_list.append((download_uri, eps_no, eps_data['file_path'], eps_data['file_name']))

        logger.error(result_list)

        return result_list

    def parse_size(self, size):
        units = {"B": 1, "KB": 10 ** 3, "MB": 10 ** 6, "GB": 10 ** 9, "TB": 10 ** 12}
        size = size.upper()
        if not re.match(r' ', size):
            size = re.sub(r'([KMGT]?B)', r' \1', size)
        number, unit = [string.strip() for string in size.split()]
        return int(float(number) * units[unit])

    @classmethod
    def has_keyword(cls, bangumi):
        return bangumi.universal is not None
