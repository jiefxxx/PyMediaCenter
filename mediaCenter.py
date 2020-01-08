#! python3

import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QTabWidget

from mediaCenter_lib.gui.dialogs import ConfirmationDialog
from mediaCenter_lib.gui.mediaplayer import MediaPlayer
from mediaCenter_lib.gui.medialibrary import MediaLibrary
from mediaCenter_lib.gui.filesharing import FileSharing
from mediaCenter_lib.gui.servermanager import ServerManager
from mediaCenter_lib.gui.videolibrary import VideoLibrary

from mediaCenter_lib.model.media import MediaModel
from mediaCenter_lib.model.movie import MovieModel
from mediaCenter_lib.model.tv import TvEpisodeModel
from mediaCenter_lib.model.filesharing import FileSharingModel
from mediaCenter_lib.model.server import ServerModel
from mediaCenter_lib.model.video import VideoModel
from mediaCenter_lib.server import ServersManager

from pythread import create_new_mode, close_all_mode
from pythread.modes import ProcessMode, AsyncioMode

from common_lib.config import configure_callback
import pyconfig

pyconfig.load("pymediacenter", proc_name="pymediacenter-gui", callback=configure_callback)

create_new_mode(ProcessMode, "httpCom", size=4)
create_new_mode(ProcessMode, "poster", size=2)
create_new_mode(AsyncioMode, "asyncio")

list_servers = ServersManager("client_"+pyconfig.get("hostname"), ["6c:f0:49:56:03:c8"])


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.models = []
        self.add_model("video", VideoModel(list_servers))
        self.add_model("media", MediaModel(list_servers))
        self.add_model("upload", FileSharingModel(list_servers))
        self.add_model("server", ServerModel(list_servers))
        self.add_model("tv_episode", TvEpisodeModel(list_servers))
        self.add_model("movie_file", MovieModel(list_servers))
        list_servers.connection_error.connect(self.on_connection_error)
        list_servers.connected.connect(self.on_connection)

        self.setMouseTracking(True)

        self.setWindowTitle("PMC - PyMediaCenter")

        self.movies = MediaLibrary(self)
        self.upload = FileSharing(self)
        self.media_player = MediaPlayer(self)
        self.server_manager = ServerManager(self)
        self.videos = VideoLibrary(self)

        self.tab = QTabWidget(self)

        self.tab.addTab(self.movies, "Media")
        self.tab.addTab(self.videos, "Videos")
        self.tab.addTab(self.upload, "Videos transfer")
        self.tab.addTab(self.server_manager, "config")

        self.stack = QStackedWidget(self)

        self.stack.addWidget(self.tab)
        self.stack.addWidget(self.media_player)

        self.setCentralWidget(self.stack)

        self.wasMaximized = False

        self.filter_connection_error = []

    def on_connection_error(self, server_name):
        if server_name in self.filter_connection_error:
            return
        self.filter_connection_error.append(server_name)
        conf = ConfirmationDialog(str(server_name) + " is not connected\r\n"
                                                     "Send a WAKE ON LAN Signal ?", self)
        if conf.exec_():
            list_servers.server(server_name).wake_on_lan()
        else:
            pass

    def on_connection(self, server_name):
        if server_name in self.filter_connection_error:
            self.filter_connection_error.remove(server_name)

    def add_model(self, name, model):
        self.models.append((name, model))

    def close_all_model(self):
        for model_name, model in self.models:
            model.close()

    def get_model(self, name):
        for model_name, model in self.models:
            if model_name == name:
                # model.refresh()
                return model
        raise Exception("Model "+name+" not found")

    def test(self, video):
        self.media_player.set_videos(video)
        self.stack.setCurrentWidget(self.media_player)

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


app = QApplication(sys.argv)
window = MainWindow()
window.showMaximized()

app.exec_()
app.closingDown()

window.close_all_model()
close_all_mode()
