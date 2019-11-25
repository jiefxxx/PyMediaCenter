import os

import requests
from PyQt5.QtCore import pyqtSignal, QVariant, QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap

import pyconfig
from mediaCenter_lib.base_model import ModelTableListDict
from pythread import threaded


class MovieModel(ModelTableListDict):
    refreshed = pyqtSignal()
    info = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        ModelTableListDict.__init__(self, [("Title", "title", False),
                                           ("Original Title", "original_title", False),
                                           ("Video ID", "video_id", False),
                                           ("Genre ID", "genre_ids", False),
                                           ("Duration", "duration", False),
                                           ("Release date", "release_date", False),
                                           ("Vote", "vote_average", False),
                                           ("Poster", "poster_path")], None)

        self.poster_mini_path = pyconfig.get("rsc.poster_mini_path")
        self.poster_original_path = pyconfig.get("rsc.poster_original_path")

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

    def get_info(self, video_id):
        response = requests.get('http://192.168.1.55:4242/movie?video_id=' + str(video_id))
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                self.info.emit(data[0])

    def get_decoration_role(self, index):
        if index.column() == 0:
            if self.poster_exists(self.list[index.row()]["poster_path"]):
                return QIcon(QPixmap(self.get_poster_path(self.list[index.row()]["poster_path"], mini=True)))
            else:
                return QIcon(QPixmap("rsc/404.jpg"))
        return QVariant()

    def get_poster_path(self, poster_path, mini=False):
        if poster_path is None:
            return "rsc/404.jpg"
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