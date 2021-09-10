from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import *
from feed_scanner.AbstractScanner import AbstractScanner
from utils.exceptions import SchedulerError
import json, socket, requests, os, re

import logging

logger = logging.getLogger(__name__)


class BANGUMI_MOE(AbstractScanner):

    def __init__(self, bangumi, episode_list):
        super(self.__class__, self).__init__(bangumi, episode_list)
        self.proxy = self._get_proxy('bangumi_moe')
        self.feed_url = 'https://bangumi.moe/api/torrent/search'
        tag_list = json.loads(bangumi.bangumi_moe)
        self.tag_list = [tag['_id'] for tag in tag_list]

    def parse_feed(self):
        logger.debug('start scan %s (%s)', self.bangumi.name, self.bangumi.id)
        eps_no_list = [eps.episode_no for eps in self.episode_list]

        timeout = socket.getdefaulttimeout()
        # set timeout is provided
        if self.timeout is not None:
            timeout = self.timeout

        r = requests.post(self.feed_url, json={'tag_id': self.tag_list}, timeout=timeout)

        if r.status_code > 399:
            raise SchedulerError('Network Error %d'.format(r.status_code))

        resp_body = r.json()

        result_list = []

        for torrent in resp_body['torrents']:
            eps_list = dict()
            for content_file in torrent['content']:
                file_path = content_file[0]
                file_size = self.parse_size(content_file[1])
                file_name = os.path.basename(file_path)
                if not file_name.endswith(('.mp4', '.mkv')):
                    continue
                eps_no = self.parse_episode_number(file_name)
                if len(resp_body['torrents']) == 1 and eps_no == -1:
                    eps_no = 1
                if eps_no in eps_no_list:
                    if eps_no not in eps_list:
                        eps_list[eps_no] = {
                            'file_path': file_path,
                            'file_name': file_name,
                            'file_size': file_size
                        }
                    else:
                        if file_size > eps_list[eps_no]['file_size']:
                            eps_list[eps_no] = {
                                'file_path': file_path,
                                'file_name': file_name,
                                'file_size': file_size
                            }
            if len(eps_list) == 0:
                continue
            torrent_url = self.generate_torrent_url(torrent['_id'], eps_list)
            for eps_no, eps_data in eps_list.items():
                result_list.append((torrent_url, eps_no, eps_data['file_path'], eps_data['file_name']))

        logger.debug(result_list)

        return result_list

    def generate_torrent_url(self, torrent_id, eps_list):
        if len(eps_list) > 1:
            eps_no_format = '{0}-{1}'.format(str(list(eps_list)[0]), str(list(eps_list)[-1]))
        else:
            eps_no_format = str(list(eps_list)[0])
        return 'https://bangumi.moe/download/torrent/{0}/{1}-{2}.torrent'.format(
            torrent_id, str(self.bangumi.id), eps_no_format)

    def parse_size(self, size):
        units = {"B": 1, "KB": 10 ** 3, "MB": 10 ** 6, "GB": 10 ** 9, "TB": 10 ** 12}
        size = size.upper()
        if not re.match(r' ', size):
            size = re.sub(r'([KMGT]?B)', r' \1', size)
        number, unit = [string.strip() for string in size.split()]
        return int(float(number) * units[unit])

    @classmethod
    def has_keyword(cls, bangumi):
        return bangumi.bangumi_moe is not None
