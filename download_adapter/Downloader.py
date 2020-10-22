from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import object


class Downloader(object):

    def __init__(self, on_download_completed):
        self.on_download_completed_callback = on_download_completed

    def download(self, magnet_uri, download_location):
        pass

    def connect_to_daemon(self):
        pass

    def remove_torrent(self, torrent_id, remove_data):
        pass

    def get_files(self, torrent_id):
        pass

    def get_complete_torrents(self):
        """
        get complete torrents
        :return: a dict which contains all complete torrents (progress = 100), key is torrent_id, value is dict {files: tuple}
        """
        pass

    """
    NOTE: You should call self.on_download_completed_callback(torrent_id) when a download finishes.
          You can register an event handler of finish event if your downloader support,
          or use polling if it doesn't support finish event pushing.
    """
