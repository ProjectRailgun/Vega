from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
import feedparser
from feed_scanner.AbstractScanner import AbstractScanner
from utils.exceptions import SchedulerError
import socket
import logging, urllib.request, urllib.error, urllib.parse, urllib.request, urllib.parse, urllib.error

logger = logging.getLogger(__name__)

logger.propagate = True

class ACG_RIP(AbstractScanner):

    def __init__(self, bangumi, episode_list):
        super(self.__class__, self).__init__(bangumi, episode_list)
        self.proxy = self._get_proxy('acg_rip')
        keywords = urllib.parse.quote_plus(bangumi.acg_rip.replace(u'+', u' '))
        self.feed_url = 'https://acg.rip/.xml?term=%s' % (keywords,)
        logger.debug(self.feed_url)

    def parse_feed(self):
        '''
        parse feed for current bangumi and find not downloaded episode in feed entries.
        this method using an async call to add torrent.
        :return: if no error when get feed None is return otherwise return the error object
        '''
        # eps no list
        logger.debug('start scan %s (%s)', self.bangumi.name, self.bangumi.id)
        eps_no_list = [eps.episode_no for eps in self.episode_list]

        default_timeout = socket.getdefaulttimeout()
        # set timeout is provided
        if self.timeout is not None:
            socket.setdefaulttimeout(self.timeout)

        # use handlers
        if self.proxy is not None:
            proxy_handler = urllib.request.ProxyHandler(self.proxy)
            feed_dict = feedparser.parse(self.feed_url, handlers=[proxy_handler])
        else:
            feed_dict = feedparser.parse(self.feed_url)

        # restore the default timeout
        if self.timeout is not None:
            socket.setdefaulttimeout(default_timeout)

        if feed_dict.bozo != 0:
            raise SchedulerError(feed_dict.bozo_exception)

        result_list = []

        for item in feed_dict.entries:
            eps_no = self.parse_episode_number(item['title'])
            if len(feed_dict.entries) == 1 and eps_no == -1:
                eps_no = 1
            if eps_no in eps_no_list:
                result_list.append((item.enclosures[0].href, eps_no, None, None))
                # d = self.add_to_download(item, eps_no)
                # d.addCallback(self.download_callback)

        return result_list

    @classmethod
    def has_keyword(cls, bangumi):
        return bangumi.acg_rip is not None
