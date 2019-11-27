#! python3

import sys


from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QTabWidget

from mediaCenter_lib.gui.mediaplayer import MediaPlayer
from mediaCenter_lib.gui.movies import Movies
from mediaCenter_lib.gui.upload_box import UploadBox
from mediaCenter_lib.gui.server_manager import ServerManager
from mediaCenter_lib.gui.videos import Videos

from mediaCenter_lib.model.genre import GenreModel
from mediaCenter_lib.model.movie import MovieModel
from mediaCenter_lib.model.upload import UploadVideoModel
from mediaCenter_lib.model.server import ServerActionModel
from mediaCenter_lib.model.video import VideoModel

from pythread import create_new_mode, close_all_mode
from pythread.modes import ProcessMode

from common_lib.config import configure_callback
import pyconfig

pyconfig.load("pymediacenter", proc_name="pymediacenter-gui", callback=configure_callback)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.models = []
        self.add_model("video", VideoModel())
        self.add_model("genre", GenreModel())
        self.add_model("movie", MovieModel(connect=self.get_model("video")))
        self.add_model("upload", UploadVideoModel())
        self.add_model("serveAction", ServerActionModel())

        self.setMouseTracking(True)

        self.setWindowTitle("PMC - PyMediaCenter")

        self.movies = Movies(self, callback=self.test)
        self.upload = UploadBox(self)
        self.media_player = MediaPlayer(self)
        self.server_manager = ServerManager(self)
        self.videos = Videos(self)

        self.tab = QTabWidget(self)

        self.tab.addTab(self.movies, "Films")
        self.tab.addTab(self.videos, "Videos")
        self.tab.addTab(self.upload, "Videos transfer")
        self.tab.addTab(self.server_manager, "config")

        self.stack = QStackedWidget(self)

        self.stack.addWidget(self.tab)
        self.stack.addWidget(self.media_player)

        self.setCentralWidget(self.stack)

        self.wasMaximized = False

    def add_model(self, name, model):
        self.models.append((name, model))

    def get_model(self, name):
        for model_name, model in self.models:
            if model_name == name:
                model.refresh()
                return model
        raise Exception("Model "+name+" not found")

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

    def full_screen(self, b=None):
        if self.isFullScreen():
            if b is None or True:
                self.showNormal()
                if self.wasMaximized:
                    self.showMaximized()

        else:
            if b is None or False:
                self.wasMaximized = self.isMaximized()
                self.showFullScreen()


create_new_mode(ProcessMode, "httpCom", size=4)
create_new_mode(ProcessMode, "poster", size=2)

app = QApplication(sys.argv)
window = MainWindow()
window.showMaximized()

app.exec_()
app.closingDown()

close_all_mode()
