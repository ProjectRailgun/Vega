# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import input
from builtins import str
from builtins import *
from builtins import object
import argparse

from sqlalchemy import func

from utils.SessionManager import SessionManager
from domain.Bangumi import Bangumi
from domain.Favorites import Favorites
from domain.WatchProgress import WatchProgress
from domain.Episode import Episode
from domain.VideoFile import VideoFile
from domain.Image import Image
import yaml
import os
import re
from utils.VideoManager import VideoManager
from utils.constants import episode_regex_tuple
from utils.image import get_dominant_color, get_dimension

class ImportTools(object):
    def __init__(self):
        pass

    def __parse_episode_number(self, eps_title):
        '''
        parse the episode number from episode title, it use a list of regular expressions. the position in the list
        is the priority of the regular expression.
        :param eps_title: the title of episode.
        :return: episode number if matched, otherwise, -1
        '''
        try:
            for regex in episode_regex_tuple:
                search_result = re.search(regex, eps_title, re.U | re.I)
                if search_result is not None:
                    return int(search_result.group(1))

            return -1
        except Exception:
            return -1

    def __episode_has_video_file(self, existed_video_files, eps):
        for video_file in existed_video_files:
            if video_file.episode_id == eps.id:
                return True

        return False

    def __video_path_already_added(self, existed_video_files, file_path):
        for video_file in existed_video_files:
            if video_file.file_path == file_path:
                return True
        return False

    def __list_file_recursively(self, download_dir):
        file_list = []
        for dp, dn, fn in os.walk(download_dir):
            for f in fn:
                (_, ext) = os.path.splitext(f)
                if (ext == '.mp4') or (ext == '.mkv'):
                    abs_path = os.path.join(dp, f)
                    relative_path = os.path.relpath(abs_path, download_dir)
                    file_list.append(relative_path)

        return file_list

    def check_and_update_bangumi_status(self, bangumi_id):
        session = SessionManager.Session()
        try:
            bangumi = session.query(Bangumi).filter(Bangumi.id == bangumi_id).one()
            episode_count = session.query(func.count(Episode.id)). \
                filter(Episode.bangumi_id == bangumi.id). \
                filter(Episode.status == Episode.STATUS_NOT_DOWNLOADED). \
                scalar()
            if (bangumi.status == Bangumi.STATUS_ON_AIR) and (episode_count == 0):
                bangumi.status = Bangumi.STATUS_FINISHED
                session.commit()
        finally:
            SessionManager.Session.remove()

    def update_bangumi(self, bangumi_id=None):
        fr = open('./config/config.yml', 'r')
        config = yaml.safe_load(fr)
        download_dir = os.path.join(config['download']['location'], str(bangumi_id))
        files = self.__list_file_recursively(download_dir)

        session = SessionManager.Session()
        try:
            eps_list = session.query(Episode).\
                filter(Episode.bangumi_id == bangumi_id).all()
            bangumi = session.query(Bangumi).\
                filter(Bangumi.id == bangumi_id).one()
            eps_no_offset = 0
            if bangumi.eps_no_offset is not None:
                eps_no_offset = bangumi.eps_no_offset

            existed_video_files = session.query(VideoFile).filter(VideoFile.bangumi_id == bangumi_id).all()

            episodes = {}
            video_files = []
            for eps in eps_list:
                # if self.__episode_has_video_file(existed_video_files, eps):
                #     continue
                episodes[eps.episode_no] = eps
                for f in files:
                    if self.__video_path_already_added(existed_video_files, f):
                        continue
                    if self.__parse_episode_number(f) + eps_no_offset == eps.episode_no:
                        eps.status = Episode.STATUS_DOWNLOADED
                        video_files.append(VideoFile(bangumi_id=bangumi_id,
                                                     episode_id=eps.id,
                                                     file_path=f,
                                                     status=VideoFile.STATUS_DOWNLOADED))
                        break
            while True:
                for eps in list(episodes.values()):
                    if not eps:
                        continue
                    episode_num = str(eps.episode_no)
                    line = episode_num + ": \t"
                    file_name = None
                    for video_file in video_files:
                        if video_file.episode_id == eps.id:
                            if file_name is None:
                                line = line + video_file.file_path
                            else:
                                line = line + "\n  \t" + video_file.file_path
                            if video_file.label is not None:
                                line = line + "\t" + video_file.label
                            file_name = video_file.file_path
                    if file_name is None:
                        line = line + "None"
                    print (line)

                print("Right? Y/N")
                x = input(">>> Input: ")
                if x == "Y":
                    video_manager = VideoManager()
                    video_manager.set_base_path(config['download']['location'])
                    for video_file in video_files:
                        for eps in list(episodes.values()):
                            if eps.id == video_file.episode_id:
                                video_manager.create_episode_thumbnail(eps, video_file.file_path, '00:00:01.000')
                                thumbnail_path = os.path.join(str(bangumi_id), 'thumbnails', str(eps.episode_no) + '.png')
                                thumbnail_file_path = os.path.join(download_dir, 'thumbnails', str(eps.episode_no) + '.png')
                                width, height = get_dimension(thumbnail_file_path)
                                eps.thumbnail_image = Image(file_path=thumbnail_path,
                                                            dominant_color=get_dominant_color(thumbnail_file_path),
                                                            width=width,
                                                            height=height)
                                meta_dict = video_manager.get_video_meta(os.path.join(video_manager.base_path, bangumi_id, video_file.file_path))
                                if meta_dict is not None:
                                    video_file.resolution_w = meta_dict['width']
                                    video_file.resolution_h = meta_dict['height']
                                    video_file.duration = meta_dict['duration']
                                    session.add(video_file)
                                # break
                    session.commit()
                    return
                else:
                    video_files = []
                    for f in files:
                        print(f)
                        x = input(">>> Episode Num and Label (separated by comma)")
                        if not x:
                            continue
                        arguments = x.split(',')
                        x = int(arguments[0])
                        label = None
                        if len(arguments) > 1:
                            label = arguments[1]
                        eps = episodes[x]
                        if not eps:
                            continue
                        eps.status = Episode.STATUS_DOWNLOADED
                        video_files.append(VideoFile(bangumi_id=bangumi_id,
                                                     episode_id=eps.id,
                                                     file_path=f,
                                                     label=label,
                                                     status=VideoFile.STATUS_DOWNLOADED))
        finally:
            SessionManager.Session.remove()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import Bangumi Tools.')
    sub_parsers = parser.add_subparsers(dest='operate')
    search_parser = sub_parsers.add_parser("search", help="Search Bangumi")
    search_parser.add_argument('name', type=str, help='Name of Bangumi')
    create_parser = sub_parsers.add_parser("create", help="Create Bangumi")
    create_parser.add_argument('id', type=int, help='Bangumi Id')
    update_parser = sub_parsers.add_parser("update", help="Update Bangumi")
    update_parser.add_argument('uuid', type=str, help='Bangumi UUID')
    args = parser.parse_args()

    import_tools = ImportTools()
    if args.operate == 'search':
        # import_tools.search_bangumi(args.name)
        print('search bangumi not supported, please use web admin')
    elif args.operate == 'create':
        # import_tools.create_bangumi(args.id)
        print('create bangumi not supported, please use web admin')
    elif args.operate == 'update':
        import_tools.update_bangumi(args.uuid)
        import_tools.check_and_update_bangumi_status(args.uuid)
