import json

import requests
import websocket
from PyQt5.QtCore import QObject, pyqtSignal

from pythread import create_new_mode, threaded
from pythread.modes import RunForeverMode


class ServerActionModel(QObject):

    def __init__(self, servers):
        QObject.__init__(self)
        self.webSocket_conn = None
        self.servers = servers

    @threaded("httpCom")
    def start_script(self, name, server_name):
        self.servers.server(server_name).start_script(name)

    def get_progress_action(self, server_name):
        return self.servers.server(server_name).progress

    def close(self):
        self.servers.close()
