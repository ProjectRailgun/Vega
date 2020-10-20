# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from builtins import object
import cfscrape, os, errno, logging, requests, pickle, traceback
logger = logging.getLogger(__name__)
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'

class DMHYRequest(object):

    def __init__(self):

        # persist request for accessing bangumi api
        self.session = cfscrape.create_scraper()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html'
        })

        session_storage_path = './.session'
        self.api_bgm_tv_session_path = session_storage_path + '/dmhy'

        try:
            if not os.path.exists(session_storage_path):
                os.makedirs(session_storage_path)
                logger.info('create session storage dir %s successfully', session_storage_path)
        except OSError as exception:
            if exception.errno == errno.EACCES:
                raise exception
            else:
                logger.warning(exception)

    def __get_cookie_from_storage(self):
        try:
            with open(self.api_bgm_tv_session_path, 'r') as f:
                self.session.cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
        except Exception as error:
            logger.warning(traceback.format_exc(error))

    def __save_cookie_to_storage(self):
        try:
            with open(self.api_bgm_tv_session_path, 'w') as f:
                pickle.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f)
        except Exception as error:
            logger.warning(traceback.format_exc(error))

    def get(self, url, proxies, timeout):
        self.__get_cookie_from_storage()
        r = self.session.get(url=url, proxies=proxies, timeout=timeout)
        self.__save_cookie_to_storage()
        return r

dmhy_request = DMHYRequest()
