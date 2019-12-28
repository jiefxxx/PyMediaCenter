import requests
from PyQt5.QtCore import pyqtSignal

from mediaCenter_lib.base_model import ModelTableListDict, ServerStateHandler
from pythread import threaded


class GenreModel(ModelTableListDict):
    def __init__(self, **kwargs):
        ModelTableListDict.__init__(self, [("Name", "name", False, None)],
                                    **kwargs)
        self.reset()

    def check_in(self, name):
        for el in self.list:
            if el['name'] == name:
                return True
        return False

    def add(self, genre):
        if not self.check_in(genre):
            self.list.append({"name": genre})
        self.reset_data(self.list)

    def reset(self):
        self.list = []
        self.list.append({"name": "Tous"})
        self.reset_data(self.list)