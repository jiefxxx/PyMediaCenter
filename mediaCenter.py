#! python3

import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QTabWidget

from mediaCenter_lib.gui.dialogs import ConfirmationDialog
from mediaCenter_lib.gui.mediaplayer import MediaPlayer
from mediaCenter_lib.gui.movies import Movies
from mediaCenter_lib.gui.tvs import Tvs
from mediaCenter_lib.gui.upload_box import UploadBox
from mediaCenter_lib.gui.server_manager import ServerManager
from mediaCenter_lib.gui.videos import Videos

from mediaCenter_lib.model.genre import GenreModel
from mediaCenter_lib.model.movie import MovieModel
from mediaCenter_lib.model.tv import TvShowModel, TvEpisodeModel
from mediaCenter_lib.model.upload import UploadVideoModel
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
#list_servers.new("local", "192.168.1.40")


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.models = []
        self.add_model("video", VideoModel(list_servers))
        self.add_model("genre", GenreModel(list_servers))
        self.add_model("movie", MovieModel(list_servers, connect=self.get_model("video")))
        self.add_model("upload", UploadVideoModel(list_servers))
        self.add_model("server", ServerModel(list_servers))
        self.add_model("tv_show", TvShowModel(list_servers))
        self.add_model("tv_episode", TvEpisodeModel(list_servers))
        list_servers.connection_error.connect(self.on_connection_error)
        list_servers.connected.connect(self.on_connection)

        self.setMouseTracking(True)

        self.setWindowTitle("PMC - PyMediaCenter")

        self.movies = Movies(self, callback=self.test)
        self.upload = UploadBox(self)
        self.media_player = MediaPlayer(self)
        self.server_manager = ServerManager(self)
        self.videos = Videos(self)
        self.tvs = Tvs(self)

        self.tab = QTabWidget(self)

        self.tab.addTab(self.movies, "Films")
        self.tab.addTab(self.tvs, "Series")
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
        if type(video) == list:
            video = video[0]
            
        uri = list_servers.server(video["server"]).get_stream(video["video_id"])
        print(uri)
        self.media_player.load(uri)
        self.stack.setCurrentWidget(self.media_player)
        print(video)

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
