import json

import requests
import websocket
from PyQt5.QtCore import QObject, pyqtSignal

from pythread import create_new_mode, threaded
from pythread.modes import RunForeverMode


class ServerActionModel(QObject):
    progress = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QObject.__init__(self)
        self.webSocket_conn = None
        create_new_mode(RunForeverMode, "ws_script", self.run_webSocket)

    @threaded("httpCom")
    def start_script(self, name):

        response = requests.get('http://192.168.1.55:4242/scripts/'+name)
        if response.status_code == 200:
            print(name, "ok")
        else:
            print(name, "pas ok")

    def run_webSocket(self):
        if self.webSocket_conn is None:
            self.webSocket_conn = websocket.WebSocket()
            self.webSocket_conn.connect('ws://192.168.1.55:4242/scripts', timeout=1)
        try:
            self.progress.emit(json.loads(self.webSocket_conn.recv()))
        except websocket._exceptions.WebSocketTimeoutException:
            pass

        return True

    def refresh(self):
        pass