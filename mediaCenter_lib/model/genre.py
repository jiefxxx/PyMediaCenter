import requests
from PyQt5.QtCore import pyqtSignal

from mediaCenter_lib.base_model import ModelTableListDict
from pythread import threaded


class GenreModel(ModelTableListDict):
    refreshed = pyqtSignal()

    def __init__(self):
        ModelTableListDict.__init__(self, [("Name", "name", False),
                                           ("ID", "id", False)],
                                    None)
        self.refresh()

    @threaded("httpCom")
    def refresh(self):
        response = requests.get('http://192.168.1.55:4242/genre')
        if response.status_code == 200:
            data = [{"name": "Tous", "id": 0}]
            data += response.json()
            self.reset_data(data)
            self.refreshed.emit()