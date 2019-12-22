import os

import requests
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap

import pyconfig
from pythread import threaded


class PosterManager:
    def __init__(self):
        self.poster_mini_path = pyconfig.get("rsc.poster_mini_path")
        self.poster_original_path = pyconfig.get("rsc.poster_original_path")

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
