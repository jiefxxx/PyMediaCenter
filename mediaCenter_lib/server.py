import json
import socket
import time

import requests
import websocket
from PyQt5.QtCore import QObject, pyqtSignal
from requests_toolbelt import MultipartEncoderMonitor
from wakeonlan import send_magic_packet

from common_lib.config import NOTIFY_REFRESH, NOTIFY_PROGRESS
from common_lib.fct import convert_size
from pythread import create_new_mode
from pythread.modes import RunForeverMode


def url_param(kwargs):
    param = "?"

    for kwarg in kwargs:
        if type(kwargs[kwarg]) == list:
            param += str(kwarg) + "="
            for el in kwargs[kwarg]:
                if el:
                    param += str(el) + ","
            param = param[:-1] + ";"
        else:
            param += str(kwarg) + "=" + str(kwargs[kwarg])
            param += ";"

    if param[-1] == ";":
        param = param[:-1]

    if len(param) == 1:
        param = ""

    return param


class ServerNotConnected(Exception):
    def __init__(self, message):
        Exception.__init__(self, message + "is not connected")


class Server(QObject):
    progress = pyqtSignal('PyQt_PyObject')

    def __init__(self, server_manager, address, name=None, ethernet=None, port=4242):
        QObject.__init__(self)
        if not name:
            name = address
        self.ethernet = ethernet
        self.manager = server_manager
        self.name, self.address, self.port = name, address, port
        self.session = requests.Session()
        self.webSocket_conn = None
        create_new_mode(RunForeverMode, "ws-" + name, self.run_webSocket)

    def wake_on_lan(self):
        if self.ethernet:
            send_magic_packet(self.ethernet)

    def _server_address(self):
        return "http://" + self.address + ":" + str(self.port)

    def get(self, path, **kwargs):
        try:
            response = self.session.get(self._server_address() + path, **kwargs)
            if response.status_code == 200:
                return response
            else:
                raise Exception(self.name + " get " + path + " --> " + str(response.status_code))
        except requests.exceptions.ConnectionError:
            raise ServerNotConnected(self.name)

    def get_json(self, path):
        return self.get(path).json()

    def get_stream(self, video_id):
        return self._server_address() + "/video/" + str(video_id) + "/stream"

    def get_movies(self, **kwargs):
        try:
            for el in self.get_json("/movie"+url_param(kwargs)):
                el["server"] = self.name
                yield el
        except ServerNotConnected:
            return

    def get_genres(self):
        try:
            return self.get_json('/genre')
        except ServerNotConnected:
            return []

    def get_videos(self, **kwargs):
        try:
            for el in self.get_json('/video' + url_param(kwargs)):
                el["server"] = self.name
                yield el
        except ServerNotConnected:
            return

    def delete_video(self, video_id):
        self.get("/video/"+str(video_id)+"/delete")

    def edit_video(self, video_id, media_type, media_id):
        self.get("/video/" + str(video_id) +
                 "/edit?media_type=" + str(media_type) +
                 "&media_id=" + str(media_id))

    def download_video(self, video_id, filename, callback=None):
        first_time = time.time()
        with self.session.get("http://" + self.address + ":" + str(self.port) +
                              "/video/" + str(video_id) + "/stream", stream=True) as r:

            if r.status_code == 200:
                size = int(r.headers['Content-length'])
                cur_size = 0
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            cur_size += len(chunk)
                            f.write(chunk)
                            bandwidth = cur_size/(time.time() - first_time)
                            progress = cur_size/size
                            if callback:
                                callback(filename,  "download " + str(round(progress*100.0, 2)) + "% " +
                                         convert_size(bandwidth) + "/s", progress)
                if callback:
                    callback(filename, "ended", 1)
            else:
                if callback:
                    callback(filename, "error", 0)

    def upload_video(self, filename, media_type, media_id, callback=None):
        if filename and media_type and media_id:

            def _callback(monitor):
                try:
                    elapsed = time.time()-_callback.first_time
                    bandwidth = monitor.bytes_read / elapsed
                except AttributeError:
                    _callback.first_time = time.time()
                    bandwidth = 0

                progress = monitor.bytes_read/monitor.len
                if monitor.bytes_read == monitor.len:
                    if callback:
                        callback(filename, "writing file to disk", 1)
                else:
                    if callback:
                        callback(filename, "upload " + str(round(progress * 100.0, 2)) + "% " +
                                 convert_size(bandwidth) + "/s", progress)

            m = MultipartEncoderMonitor.from_fields(
                fields={"json": json.dumps({"media_id": media_id,
                                            "ext": filename.split(".")[-1]}),
                        'video': open(filename, 'rb')},
                callback=_callback
            )

            try:
                r = self.session.post("http://" + self.address + ":" + str(self.port) +
                                      "/upload?media_type="+str(media_type), data=m,
                                      headers={'Content-Type': m.content_type})
                if r.status_code == 200:
                    if callback:
                        callback(filename, "ended", 1)
                else:
                    if callback:
                        callback(filename, "error", 0)
            except requests.exceptions.ConnectionError:
                if callback:
                    callback(filename, "error", 0)
        else:
            if callback:
                callback(filename, "data invalid", 0)

    def start_script(self, name):
        self.get('/scripts/'+name)

    def run_webSocket(self):
        if self.webSocket_conn is None:
            try:
                self.webSocket_conn = websocket.WebSocket()
                self.webSocket_conn.connect('ws://' + self.address + ":" + str(self.port) + '/scripts', timeout=1)
                self.manager.connected.emit(self.name)
            except (ConnectionRefusedError, websocket._exceptions.WebSocketAddressException, socket.timeout):
                self.webSocket_conn = None
                self.manager.connection_error.emit(self.name)
                time.sleep(5)
                return True

        try:
            data = json.loads(self.webSocket_conn.recv())
            if data["id"] == NOTIFY_REFRESH:
                self.manager.refresh.emit(self.name, data["data"])
            elif data["id"] == NOTIFY_PROGRESS:
                self.progress.emit(data["data"])
        except websocket._exceptions.WebSocketTimeoutException:
            pass
        except websocket._exceptions.WebSocketConnectionClosedException:
            self.webSocket_conn = None
            self.manager.disconnected.emit(self.name)

        return True


class ServersManager(QObject):
    connected = pyqtSignal('PyQt_PyObject')
    connection_error = pyqtSignal('PyQt_PyObject')
    disconnected = pyqtSignal('PyQt_PyObject')
    refresh = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')

    def __init__(self):
        QObject.__init__(self)
        self.servers_list = []

    def new(self, name, address, **kwargs):
        self.servers_list.append(Server(self, address, name, **kwargs))

    def server(self, name):
        for server in self.servers_list:
            if server.name == name:
                return server
        raise Exception("Server not found")

    def all(self):
        return self.servers_list







