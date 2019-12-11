import json

import requests
import websocket
from PyQt5.QtCore import QObject, pyqtSignal

from mediaCenter_lib.base_model import ServerStateHandler, ModelTableListDict
from pythread import create_new_mode, threaded
from pythread.modes import RunForeverMode


class ServerModel(ServerStateHandler, ModelTableListDict):
    refreshed = pyqtSignal()

    def __init__(self, servers, **kwargs):
        ModelTableListDict.__init__(self, [("ServerName", "name", False),
                                           ("SeverAddress", 'addr', False)], **kwargs)

        ServerStateHandler.__init__(self, servers)
        self.refresh()

    def refresh(self):
        data = []
        for server in self.servers.all(connected=True):
            data.append({"name": server.name, "addr": server.address+":"+str(server.port)})

        self.reset_data(data)
        self.refreshed.emit()

    def on_connection(self, server_name):
        self.refresh()

    def on_disconnection(self, server_name):
        self.refresh()

    @threaded("httpCom")
    def start_script(self, name, server_name):
        self.servers.server(server_name).start_script(name)

    def get_progress_action(self, server_name):
        return self.servers.server(server_name).progress

    def get_last_progress(self, server_name):
        return self.servers.server(server_name).last_data_progress

    def close(self):
        self.servers.close()
