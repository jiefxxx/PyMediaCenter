#! python3
import os
import sys
from pathlib import Path

import requests
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QTabWidget

from mediaCenter_lib.gui.mediaplayer import MediaPlayer
from mediaCenter_lib.gui.movies import Movies
from mediaCenter_lib.gui.upload_box import UploadBox

from pythread.threadMananger import ThreadMananger, threadedFunction


class MainWindow(QMainWindow):

    def __init__(self, root, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.root = root
        self.setMouseTracking(True)

        self.setWindowTitle("PMC - PyMediaCenter")

        self.movies = Movies(self, callback=self.test)
        self.upload = UploadBox(self)
        self.media_player = MediaPlayer(self)

        self.tab = QTabWidget(self)

        self.tab.root = self.root
        self.tab.addTab(self.movies, "Films")
        self.tab.addTab(self.upload, "Uploads")

        self.stack = QStackedWidget(self)
        self.stack.root = self.root

        self.stack.addWidget(self.tab)
        self.stack.addWidget(self.media_player)

        self.setCentralWidget(self.stack)

        self.wasMaximized = False

    def test(self, movie):
        print("http://192.168.1.55:4242/video/" + str(movie["video_id"]) + "/stream")
        self.media_player.load("http://192.168.1.55:4242/video/" + str(movie["video_id"]) + "/stream")
        self.stack.setCurrentWidget(self.media_player)
        print(movie)

    def play_row(self, path):
        self.media_player.load(path)
        self.stack.setCurrentWidget(self.media_player)

    def on_close_player(self):
        self.stack.setCurrentWidget(self.tab)

    def full_screen(self, b=True):
        if self.isFullScreen():
            if b:
                self.showNormal()
                if self.wasMaximized:
                    self.showMaximized()

        else:
            if bool is None or False:
                self.wasMaximized = self.isMaximized()
                self.showFullScreen()


class Root(ThreadMananger):
    def __init__(self):
        ThreadMananger.__init__(self, 1, debug=False)
        self.movies = None
        self.cache = False

        self.app_data_path = None
        self.poster_mini_path = None
        self.poster_original_path = None

        self.init_app_data()

        self.window = MainWindow(self)
        self.window.showMaximized()

    def init_app_data(self):
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

    @threadedFunction(0)
    def get_movies(self, signal):
        response = requests.get('http://192.168.1.55:4242/movie?columns=video_id,title,genre_ids,original_title,'
                                'duration,release_date,vote_average,poster_path')
        if response.status_code == 200:
            data = response.json()
            signal.emit(data)
            for movie in data:
                self.get_poster(movie["poster_path"])
            signal.emit(data)

    @threadedFunction(0)
    def get_genres(self, signal):
        response = requests.get('http://192.168.1.55:4242/genre')
        if response.status_code == 200:
            signal.emit(response.json())

    def get_poster_path(self, poster_path, mini=False):
        if mini:
            return self.poster_mini_path + poster_path
        else:
            return self.poster_original_path + poster_path

    def poster_exists(self, poster_path):
        if poster_path is None:
            return False
        if not os.path.exists(self.get_poster_path(poster_path, mini=True)):
            return False
        if not os.path.exists(self.get_poster_path(poster_path)):
            return False
        return True

    def get_poster(self, poster_path):
        if poster_path is None:
            return
        original_path = self.poster_original_path + poster_path
        mini_path = self.poster_mini_path + poster_path

        if not os.path.exists(original_path) or not os.path.exists(mini_path):
            print("get poster", poster_path)

            response = requests.get("https://image.tmdb.org/t/p/original" + poster_path, stream=True)
            if response.status_code == 200:
                with open(original_path, 'wb') as f:
                    for chunk in response:
                        f.write(chunk)
                pixmap = QPixmap(original_path).scaled(QSize(154, 231), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                pixmap.save(mini_path, "JPG")


app = QApplication(sys.argv)
controller = Root()
try:
    app.exec_()
except KeyboardInterrupt:
    pass
del controller.window
controller.close()
app.closingDown()
