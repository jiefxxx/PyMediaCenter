import json
import os
import sys
import time
from pathlib import Path

import requests
from PyQt5.QtCore import QVariant, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from requests_toolbelt.multipart.encoder import MultipartEncoderMonitor
from PyQt5.QtWidgets import QFileDialog

import pyconfig
from common_lib.config import MEDIA_TYPE_MOVIE
from common_lib.fct import convert_size
from common_lib.videos_info import SearchMovie
from mediaCenter_lib.base_model import ModelTableListDict
from pythread import threaded


class GenreModel(ModelTableListDict):
    refreshed = pyqtSignal()

    def __init__(self, parent):
        ModelTableListDict.__init__(self, [("Name", "name", False),
                                           ("ID", "id", False)],
                                    parent)
        self.refresh()

    @threaded("httpCom")
    def refresh(self):
        response = requests.get('http://192.168.1.55:4242/genre')
        if response.status_code == 200:
            data = [{"name": "Tous", "id": 0}]
            data += response.json()
            self.reset_data(data)
            self.refreshed.emit()


class MovieModel(ModelTableListDict):
    refreshed = pyqtSignal()

    def __init__(self, parent):
        ModelTableListDict.__init__(self, [("Title", "title", False),
                                           ("Original Title", "original_title", False),
                                           ("Video ID", "video_id", False),
                                           ("Genre ID", "genre_ids", False),
                                           ("Duration", "duration", False),
                                           ("Release date", "release_date", False),
                                           ("Vote", "vote_average", False),
                                           ("Poster", "poster_path")], parent)

        if sys.platform.startswith('linux'):
            self.app_data_path = str(Path.home())+"/.pymediacenter"
        elif sys.platform == "win32":
            self.app_data_path = os.path.expandvars(r'%LOCALAPPDATA%')+"/pymediacenter"
        else:
            raise Exception("unknow système")

        poster_path = self.app_data_path + "/poster"

        self.poster_mini_path = poster_path + "/mini"
        self.poster_original_path = poster_path + "/original"

        if not os.path.exists(self.app_data_path):
            print("Create ", self.app_data_path)
            os.mkdir(self.app_data_path)
        if not os.path.exists(poster_path):
            print("Create ", poster_path)
            os.mkdir(poster_path)
        if not os.path.exists(self.poster_mini_path):
            print("Create ", self.poster_mini_path)
            os.mkdir(self.poster_mini_path)
        if not os.path.exists(self.poster_original_path):
            print("Create ", self.poster_original_path)
            os.mkdir(self.poster_original_path)

        self.refresh()

    @threaded("httpCom")
    def refresh(self):
        requested_key = ""
        for key in self.get_keys():
            requested_key += key+","
        requested_key = requested_key[:-1]
        response = requests.get('http://192.168.1.55:4242/movie?columns='+requested_key)
        if response.status_code == 200:
            data = response.json()
            self.reset_data(data)
        self.refreshed.emit()

    def get_decoration_role(self, index):
        if index.column() == 0:
            if self.poster_exists(self.list[index.row()]["poster_path"]):
                return QIcon(QPixmap(self.get_poster_path(self.list[index.row()]["poster_path"], mini=True)))
            else:
                return QIcon(QPixmap("rsc/404.jpg"))
        return QVariant()

    def get_poster_path(self, poster_path, mini=False):
        if mini:
            return self.poster_mini_path + poster_path
        else:
            return self.poster_original_path + poster_path

    def poster_exists(self, poster_path):
        if poster_path is None:
            return False
        if not os.path.exists(self.get_poster_path(poster_path, mini=True)):
            self.get_poster(poster_path)
            return False
        if not os.path.exists(self.get_poster_path(poster_path)):
            self.get_poster(poster_path)
            return False
        return True

    @threaded("poster")
    def get_poster(self, poster_path):
        print("get poster", poster_path)
        if poster_path is None:
            return
        original_path = self.poster_original_path + poster_path
        mini_path = self.poster_mini_path + poster_path

        if not os.path.exists(original_path) or not os.path.exists(mini_path):

            response = requests.get("https://image.tmdb.org/t/p/original" + poster_path, stream=True)
            if response.status_code == 200:
                with open(original_path, 'wb') as f:
                    for chunk in response:
                        f.write(chunk)
                pixmap = QPixmap(original_path).scaled(QSize(154, 231), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                pixmap.save(mini_path, "JPG")


class TmdbModel(ModelTableListDict):
    def __init__(self, api_key, parent):
        ModelTableListDict.__init__(self, [("Title", "title", False),
                                           ("Release date", "release_date", False)], parent)
        self.search = SearchMovie(pyconfig.get("tmdb.api_key"))

    @threaded("httpCom")
    def on_search(self, text, year=None):
        self.begin_busy()
        self.clear()
        for movie in self.search.search_movie(text, year, language=pyconfig.get("language")):
            self.add_data(movie)
        self.end_busy()


class UploadVideoModel(ModelTableListDict):
    def __init__(self, parent):
        ModelTableListDict.__init__(self, [("Path", "path", False),
                                           ("Size", "size", False),
                                           ("Edited", "edited", False),
                                           ("Status", "status", False)], parent)

    def add(self, files=None):
        if files is None:
            files, _ = QFileDialog.getOpenFileNames(self.parent(), "get videos", "",
                                                    "Video files (*.asf *.avi *.flv *.m4v *.mkv *.mov *.mp4 *.mpg "
                                                    "*.mpeg)")
        for file in files:
            video, _ = self.get_by_path(file)
            if video is None:
                self.add_data({"path": file, "size": convert_size(os.path.getsize(file))})

    def get_by_path(self, path):
        for i in range(0, len(self.list)):
            if self.list[i]["path"] == path:
                return self.list[i], self.createIndex(i, 0)
        return None, None

    def set_info(self, index, info):
        video = self.data(index)
        video["id"] = info["id"]
        video["media_type"] = MEDIA_TYPE_MOVIE
        video["edited"] = "find movie : " + info["title"] + " " + info["release_date"][:4]
        self.setData(index, video)

    def _status(self, path, status):
        video, index = self.get_by_path(path)
        if video is None:
            return
        video["status"] = status
        self.setData(index, video)

    def send(self, index):
        self._status(index, "Queued")
        self.threaded_send(index)

    @threaded("upload")
    def threaded_send(self, index):
        self.begin_busy()
        video = self.data(index)
        path = video.get("path")
        media_type = video.get("media_type")
        media_id = video.get("id")
        if path and media_type and media_id:

            def callback(monitor):
                try:
                    elapsed = time.time()-callback.first_time
                    bandwidth = round((monitor.bytes_read / elapsed)/(1024*1024), 2)
                except AttributeError:
                    callback.first_time = time.time()
                    bandwidth = 0

                progress = round(monitor.bytes_read/monitor.len*100.0, 2)
                if monitor.bytes_read == monitor.len:
                    self._status(path, "writing file to disk...")
                else:
                    self._status(path, "Sending... ("+str(progress)+"): "+str(bandwidth)+"MB/S")

            m = MultipartEncoderMonitor.from_fields(
                fields={"json": json.dumps({"media_id": media_id,
                                            "ext": path.split(".")[-1]}),
                        'video': open(path, 'rb')},
                callback=callback
            )

            self._status(path, "Sending...")
            try:
                r = requests.post("http://192.168.1.55:4242/upload?media_type="+str(media_type), data=m,
                                  headers={'Content-Type': m.content_type})
                if r.status_code == 200:
                    self._status(path, "Send completed")
                else:
                    self._status(path, "Send error")
            except requests.exceptions.ConnectionError:
                self._status(path, "Send connection error")
        else:
            self._status(path, "Invalid data")
        self.end_busy()
