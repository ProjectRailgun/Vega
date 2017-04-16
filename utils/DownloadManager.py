from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import threads
from download_adapter.DelugeDownloader import DelugeDownloader
from domain.TorrentFile import TorrentFile
from domain.Episode import Episode
from domain.Bangumi import Bangumi
from domain.VideoFile import VideoFile
from utils.SessionManager import SessionManager
from utils.VideoManager import video_manager
from datetime import datetime
from sqlalchemy import exc
import logging

logger = logging.getLogger(__name__)


class DownloadManager:

    def __init__(self, downloader_cls):
        self.downloader = downloader_cls(self.on_download_completed)

    def connect(self):
        '''
        connect to a downloader daemon, currently use deluge.
        :return: a Deferred object
        '''
        return self.downloader.connect_to_daemon()


    def on_download_completed(self, torrent_id):
        logger.info('Download complete: %s', torrent_id)

        def create_thumbnail(episode, file_path):
            time = '00:00:01.000'
            video_manager.create_episode_thumbnail(episode, file_path, time)

        def update_video_files(file_path_list):
            session = SessionManager.Session()
            try:
                result = session.query(VideoFile, Episode).\
                    join(Episode).\
                    filter(VideoFile.torrent_id == torrent_id).\
                    all()
                for (video_file, episode) in result:
                    for file_path in file_path_list:
                        if video_file.file_name is not None and video_file.file_path is None and file_path.endswith(video_file.file_name):
                            video_file.file_path = file_path
                            video_file.status = VideoFile.STATUS_DOWNLOADED
                            episode.update_time = datetime.now()
                            episode.status = Episode.STATUS_DOWNLOADED
                            create_thumbnail(episode, file_path)
                            break
                        elif video_file.file_path is not None and file_path == video_file.file_path:
                            video_file.status = VideoFile.STATUS_DOWNLOADED
                            episode.update_time = datetime.now()
                            episode.status = Episode.STATUS_DOWNLOADED
                            create_thumbnail(episode, file_path)
                            break

                session.commit()
            except exc.DBAPIError as db_error:
                if db_error.connection_invalidated:
                    session.rollback()
            finally:
                SessionManager.Session.remove()

        def get_files(files):
            print files
            file_path_list = [file['path'] for file in files]
            threads.deferToThread(update_video_files, file_path_list)

        def fail_to_get_files(result):
            logger.warn('fail to get files of %s', torrent_id)
            logger.warn(result)

        d = self.downloader.get_files(torrent_id)
        d.addCallback(get_files)
        d.addErrback(fail_to_get_files)

    @inlineCallbacks
    def download(self, download_url, download_location):
        self.downloader.download(download_url, download_location)

    @inlineCallbacks
    def remove_torrents(self, torrent_id_list, remove_data):
        result_list = []
        for torrent_id in torrent_id_list:
            result = yield self.downloader.remove_torrent(torrent_id, remove_data)
            result_list.append(result)
        returnValue(result_list)

download_manager = DownloadManager(DelugeDownloader)
