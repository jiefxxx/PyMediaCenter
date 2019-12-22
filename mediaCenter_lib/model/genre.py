import requests
from PyQt5.QtCore import pyqtSignal

from mediaCenter_lib.base_model import ModelTableListDict, ServerStateHandler
from pythread import threaded


class GenreModel(ServerStateHandler, ModelTableListDict):

    def __init__(self, servers, **kwargs):
        ModelTableListDict.__init__(self, [("Name", "name", False, None),
                                           ("ID", "id", False, None)],
                                    **kwargs)
        ServerStateHandler.__init__(self, servers)
        self.refresh()

    def on_connection(self, server_name):
        self.refresh()

    def on_disconnection(self, server_name):
        self.refresh()

    @threaded("httpCom")
    def refresh(self):
        server = list(self.servers.all())[0]
        data = list(server.get_genres())
        data += [{"name": "Tous", "id": 0}]
        self.reset_data(data)
        self.end_refreshed()
