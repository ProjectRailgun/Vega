from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library

from os import path
standard_library.install_aliases()
from builtins import *
from .Downloader import Downloader
from yaml import safe_load
from clutch import Client
from twisted.internet import defer
from utils.exceptions import SchedulerError


class TransmissionDownloader(Downloader):

    def __init__(self, on_download_completed):
        super().__init__(on_download_completed)

        fr = open('./config/config.yml', 'r')
        config = safe_load(fr)
        self.transmissionConfig = config['transmission']

        self.__client = Client
        self.__disconnect_callback = BaseException

    def __on_connect_success(self, result):
        """
        Add post-actions for connect success
        """
        return result

    def __on_connect_fail(self, result):
        raise Exception('TransmissionDownloader: Connecting to transmission daemon failed')

    def connect_to_daemon(self):
        try:
            self.__client = Client(
                address="http://{host}:{port}/transmission/rpc".format(
                    host=self.transmissionConfig['host'],
                    port=self.transmissionConfig['port'],
                ),
                username=self.transmissionConfig['username'],
                password=self.transmissionConfig['password'],
            )
        except Exception as error:
            return defer.fail(SchedulerError('TransmissionDownloader: Connecting to transmission daemon failed: ' + format(error)))
        return defer.succeed('TransmissionDownloader: Connecting to transmission daemon succeed')

    def set_on_disconnect_callback(self, callback):
        """
        We can not detect disconnecting since transmission JSON-RPC is stateless,
        so we save the callback func and call it when a TransmissionError raises.
        """
        self.__disconnect_callback = callback

    def __on_download_completed(self, torrent_id):
        self.__on_download_completed_callback(torrent_id)

    def __url_type(self, download_url):
        if download_url.startswith('magnet:?'):
            return 'magnet'
        if download_url.endswith('.torrent'):
            return 'torrent'
        return 'unknown'

    def download(self, download_url, download_location):
        url_type = self.__url_type(download_url)
        if url_type == 'unknown':
            raise SchedulerError('Unsupported url format')
        try:
            torrent = self.__client.torrent.add({"filename": download_url, "download_dir": download_location})
            if torrent.arguments.torrent_added:
                torrent_id = torrent.arguments.torrent_added.id
            elif torrent.arguments.torrent_duplicate:
                torrent_id = torrent.arguments.torrent_duplicate.id
            else:
                return defer.fail(SchedulerError('TransmissionDownloader: Add torrent failed: unexpected RPC response content'))
        except Exception as error:
            return defer.fail(SchedulerError('TransmissionDownloader: Add torrent failed: ' + format(error)))
        return defer.succeed(torrent_id)

    def get_files(self, torrent_id):
        try:
            resp = self.__client.torrent.accessor(fields=['download_dir', 'files'], ids=[torrent_id]).dict(exclude_none=True)
            files = []
            for file in resp['arguments']['torrents'][0]['files']:
                files.append({'path': path.join(resp['arguments']['torrents'][0]['download_dir'], file['name'])})
        except Exception as error:
            return defer.fail(SchedulerError('TransmissionDownloader: Get torrent files failed: ' + format(error)))
        return defer.succeed(files)

    def remove_torrent(self, torrent_id, remove_data):
        try:
            remove = self.__client.torrent.remove(ids=[torrent_id], delete_local_data=remove_data).dict(exclude_none=True)
        except Exception as error:
            return defer.fail(SchedulerError('TransmissionDownloader: Get torrent files failed: ' + format(error)))
        return defer.succeed(remove)

    def get_complete_torrents(self):
        """
        get complete torrents
        :return: a dict which contains all complete torrents (progress = 100), key is torrent_id, value is dict {files: tuple}
        """
        try:
            resp = self.__client.torrent.accessor(fields=['id', 'done_date', 'download_dir', 'files']).dict(exclude_none=True)
            torrents = {}
            for torrent in resp['arguments']['torrents']:
                if torrent['done_date'] is not 0:
                    files = []
                    for file in torrent['files']:
                        files.append({'path': path.join(torrent['download_dir'], file['name'])})
                    torrents[torrent['id']] = {'files': files}
        except Exception as error:
            return defer.fail(SchedulerError('TransmissionDownloader: Get complete torrents failed: ' + format(error)))
        return defer.succeed(torrents)
