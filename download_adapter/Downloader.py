from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from future import standard_library
standard_library.install_aliases()
from builtins import *
from builtins import object
class Downloader(object):

    def download(self, magnet_uri, download_location):
        pass

    def connect_to_daemon(self):
        pass

    def remove_torrent(self, torrent_id, remove_data):
        pass

    def get_files(self, torrent_id):
        pass

    def get_complete_torrents(self):
        pass
