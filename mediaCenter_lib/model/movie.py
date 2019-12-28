import os

import requests
from PyQt5.QtCore import pyqtSignal, QVariant, QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap

import pyconfig
from mediaCenter_lib.base_model import ModelTableListDict, ServerStateHandler
from mediaCenter_lib.model.genre import GenreModel
from pythread import threaded


class MovieModel(ServerStateHandler, ModelTableListDict):
    info = pyqtSignal('PyQt_PyObject')

    def __init__(self, servers,  **kwargs):
        ModelTableListDict.__init__(self, [("#", None, False, None),
                                           ("Title", "title", False, None),
                                           ("Original Title", "original_title", False, None),
                                           ("Video ID", "video_id", False, None),
                                           ("Genres", "genre_name", False, None),
                                           ("Duration", "duration", False, None),
                                           ("Release date", "release_date", False, None),
                                           ("Vote", "vote_average", False, None),
                                           ("Poster", "poster_path", False, None)], **kwargs)

        self.poster_mini_path = pyconfig.get("rsc.poster_mini_path")
        self.poster_original_path = pyconfig.get("rsc.poster_original_path")

        ServerStateHandler.__init__(self, servers)
        self.genres_model = GenreModel()
        self.refresh()

    def on_connection(self, server_name):
        self.refresh()

    def on_disconnection(self, server_name):
        self.refresh()

    def on_refresh(self, server_name, section):
        if section == "movies":
            self.refresh()

    @threaded("httpCom")
    def refresh(self):
        data = []
        self.genres_model.reset()
        for server in self.servers.all():
            for movie in server.get_movies(columns=list(self.get_keys())):
                for genre in movie["genre_name"]:
                    self.genres_model.add(genre)
                data.append(movie)
        self.reset_data(data)
        self.end_refreshed()

    @threaded("httpCom")
    def get_info(self, video):
        self.info.emit(list(self.servers.server(video["server"]).get_movies(video_id=video["video_id"]))[0])

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