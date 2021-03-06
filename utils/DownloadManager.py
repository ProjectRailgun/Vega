from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import *
from builtins import object
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import threads
from domain.TorrentFile import TorrentFile
from domain.Episode import Episode
from domain.Bangumi import Bangumi
from domain.VideoFile import VideoFile
from domain.Image import Image
from utils.SessionManager import SessionManager
from utils.VideoManager import video_manager
from datetime import datetime
from sqlalchemy import exc
from utils.image import get_dominant_color, get_dimension
from os import path
from rpc.rpc_interface import episode_downloaded
from utils.exceptions import SchedulerError
import logging
import yaml

logger = logging.getLogger(__name__)

# loading specific downloader implementation
fr = open('./config/config.yml', 'r')
config = yaml.safe_load(fr)
if not config['downloader'] in ('deluge', 'transmission'):
    raise SchedulerError('Invalid downloader value in config.yml')
if config['downloader'] == 'deluge':
    from download_adapter.DelugeDownloader import DelugeDownloader
if config['downloader'] == 'transmission':
    from download_adapter.TransmissionDownloader import TransmissionDownloader


class DownloadManager(object):

    def __init__(self, downloader_cls):
        self.downloader = downloader_cls(self.on_download_completed)
        fr = open('./config/config.yml', 'r')
        config = yaml.safe_load(fr)
        self.base_path = config['download']['location']

    def connect(self):
        """
        connect to a downloader daemon, currently use deluge.
        :return: a Deferred object
        """
        return self.downloader.connect_to_daemon()

    def set_disconnect_cb(self, cb):
        self.downloader.set_on_disconnect_callback(cb)

    def on_download_completed(self, torrent_id):
        logger.info('Download complete: %s', torrent_id)

        def create_thumbnail(episode, file_path):
            time = '00:00:02.000'
            video_manager.create_episode_thumbnail(episode, file_path, time)
            try:
                thumbnail_path = path.join(str(episode.bangumi_id), 'thumbnails', str(episode.episode_no) + '.png')
                thumbnail_file_path = path.join(self.base_path, thumbnail_path)
                color = get_dominant_color(thumbnail_file_path)
                width, height = get_dimension(thumbnail_file_path)
                episode.thumbnail_image = Image(file_path=thumbnail_path,
                                                dominant_color=color,
                                                width=width,
                                                height=height)
                episode.thumbnail_color = color
            except Exception as error:
                logger.error(error, exc_info=True)

        def update_video_meta(video_file):
            meta = video_manager.get_video_meta(path.join(self.base_path, str(video_file.bangumi_id), video_file.file_path))
            if meta is not None:
                video_file.duration = meta.get('duration')
                video_file.resolution_w = meta.get('width')
                video_file.resolution_h = meta.get('height')

        def update_video_files(file_list):
            session = SessionManager.Session()
            episode_id = None
            try:
                result = session.query(VideoFile, Episode).\
                    join(Episode).\
                    filter(VideoFile.torrent_id == torrent_id).\
                    filter(Episode.id == VideoFile.episode_id).\
                    all()
                for (video_file, episode) in result:
                    if video_file.file_path is None and video_file.file_name is None:
                        if len(file_list) == 1:
                            # only one file
                            file_path = file_list[0]['path']
                        elif len(file_list) > 1:
                            max_size = file_list[0]['size']
                            main_file = file_list[0]
                            for file in file_list:
                                if not file['path'].endswith(('.mp4', '.mkv')):
                                    continue
                                if file['size'] > max_size:
                                    main_file = file

                            file_path = main_file['path']
                        else:
                            logger.warning('no file found in %s', torrent_id)
                            continue
                        video_file.file_path = file_path
                        video_file.status = VideoFile.STATUS_DOWNLOADED
                        episode.update_time = datetime.utcnow()
                        episode.status = Episode.STATUS_DOWNLOADED
                        create_thumbnail(episode, file_path)
                        update_video_meta(video_file)
                        episode_id = str(episode.id)
                    else:
                        file_path_list = [file['path'] for file in file_list]
                        for file_path in file_path_list:
                            if video_file.file_name is not None and video_file.file_path is None and file_path.endswith(video_file.file_name):
                                video_file.file_path = file_path
                                video_file.status = VideoFile.STATUS_DOWNLOADED
                                episode.update_time = datetime.utcnow()
                                episode.status = Episode.STATUS_DOWNLOADED
                                create_thumbnail(episode, file_path)
                                update_video_meta(video_file)
                                episode_id = str(episode.id)
                                break
                            elif video_file.file_path is not None and file_path == video_file.file_path:
                                video_file.status = VideoFile.STATUS_DOWNLOADED
                                episode.update_time = datetime.utcnow()
                                episode.status = Episode.STATUS_DOWNLOADED
                                create_thumbnail(episode, file_path)
                                update_video_meta(video_file)
                                episode_id = str(episode.id)
                                break

                session.commit()
                return episode_id
            except exc.DBAPIError as db_error:
                if db_error.connection_invalidated:
                    session.rollback()
            finally:
                SessionManager.Session.remove()

        @inlineCallbacks
        def get_files(files):
            logger.debug(files)
            episode_id = yield threads.deferToThread(update_video_files, files)
            # send an event to web_hook
            episode_downloaded(episode_id=episode_id)

        def fail_to_get_files(result):
            logger.warning('fail to get files of %s', torrent_id)
            logger.warning(result)

        d = self.downloader.get_files(torrent_id)
        d.addCallback(get_files)
        d.addErrback(fail_to_get_files)

    @inlineCallbacks
    def download(self, download_url, download_location):
        torrent_id = yield self.downloader.download(download_url.strip(), download_location)
        returnValue(torrent_id)

    @inlineCallbacks
    def remove_torrents(self, torrent_id_list, remove_data):
        result_list = []
        for torrent_id in torrent_id_list:
            result = yield self.downloader.remove_torrent(torrent_id, remove_data)
            result_list.append(result)
        returnValue(result_list)

    @inlineCallbacks
    def get_complete_torrents(self):
        torrent_dict = yield self.downloader.get_complete_torrents()
        returnValue(torrent_dict)


# initialize specific downloader
if config['downloader'] == 'deluge':
    download_manager = DownloadManager(DelugeDownloader)
if config['downloader'] == 'transmission':
    download_manager = DownloadManager(TransmissionDownloader)
