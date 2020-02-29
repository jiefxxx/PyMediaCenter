import asyncio
import json
import sys
import time
import traceback
import requests
import websockets

from wakeonlan import send_magic_packet
from PyQt5.QtCore import QObject, pyqtSignal
from requests_toolbelt import MultipartEncoderMonitor


import pythread
from common_lib.config import NOTIFY_REFRESH, NOTIFY_TASK, MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV
from common_lib.fct import convert_size
from mediaCenter_lib.model.server import ServerTasksModel
from pynet.multicast import create_multicast_server


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
    task = pyqtSignal('PyQt_PyObject')

    def __init__(self, server_manager, address, name, ethernet=None, port=4242):
        QObject.__init__(self)
        if not name:
            name = address

        self.ethernet = ethernet
        self.manager = server_manager

        self.name, self.address, self.port = name, address, port
        self.session = requests.Session()

        self.webSocket_conn = None
        self.last_data_progress = None

        self.is_running = True
        self.model = ServerTasksModel(server_manager, self)
        self.websocket = self.start_websocket()

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

    def get_tasks(self):
        try:
            return list(self.get_json("/scripts/state"))

        except ServerNotConnected:
            return

    def get_stream(self, video_id):
        return self._server_address() + "/media_stream"+url_param({"video_id": video_id})

    def get_movies(self, **kwargs):
        try:
            for el in self.get_json("/media_info/movies"+url_param(kwargs)):
                el["server"] = self.name
                yield el
        except ServerNotConnected:
            return

    def get_tv_shows(self, **kwargs):
        try:
            for el in self.get_json("/media_info/tv_shows"+url_param(kwargs)):
                el["server"] = self.name
                yield el
        except ServerNotConnected:
            return

    def get_tv_episodes(self, **kwargs):
        try:
            for el in self.get_json("/media_info/episodes"+url_param(kwargs)):
                el["server"] = self.name
                yield el
        except ServerNotConnected:
            return

    def get_videos(self, **kwargs):
        try:
            for el in self.get_json("/media_info/videos"+url_param(kwargs)):
                el["server"] = self.name
                yield el
        except ServerNotConnected:
            return

    def delete_video(self, video_id):
        self.get("/video/"+str(video_id)+"/delete")

    def edit_movie(self, video_id, movie_id, copy=False):
        self.get("/video/" + str(video_id) +
                 "/edit?media_type=" + str(MEDIA_TYPE_MOVIE) +
                 "&movie_id=" + str(movie_id) +
                 "&copy=" + str(int(copy)))

    def edit_last_time(self, video_id, last_time):
        self.get("/video/" + str(video_id) +
                 "/last_time?time=" + str(last_time))

    def edit_tv(self, video_id, tv_id, season, episode, copy=False):
        self.get("/video/" + str(video_id) +
                 "/edit?media_type=" + str(MEDIA_TYPE_TV) +
                 "&tv_id=" + str(tv_id) +
                 "&season=" + str(season) +
                 "&episode=" + str(episode) +
                 "&copy=" + str(int(copy)))

    def download_video(self, video_id, filename, callback=None):
        first_time = time.time()
        with self.session.get("http://" + self.address + ":" + str(self.port) +
                              "/media_stream"+url_param({"video_id": video_id}), stream=True) as r:

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
                                            "ext": filename.split(".")[-1],
                                            "filename": filename.split("/")[-1]}),
                        'video': open(filename, 'rb')},
                callback=_callback
            )

            try:
                r = self.session.post("http://" + self.address + ":" + str(self.port) +
                                      "/media_stream?media_type="+str(media_type), data=m,
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
        print("start_task", name)
        self.get('/scripts/'+name)

    @pythread.threaded("asyncio")
    async def start_websocket(self):
        while self.is_running:
            try:
                uri = 'ws://' + self.address + ":" + str(self.port) + '/scripts'
                async with websockets.connect(uri) as _websocket:
                    self.webSocket_conn = _websocket
                    self.manager.connected.emit(self.name)
                    while self.is_running:
                        try:
                            data = await asyncio.wait_for(_websocket.recv(), timeout=5)
                            data = json.loads(data)
                            if data["id"] == NOTIFY_REFRESH:
                                self.manager.refresh.emit(self.name, data["data"])
                                print("refresh", self.name, data["data"])
                            elif data["id"] == NOTIFY_TASK:
                                self.last_data_progress = data["data"]
                                self.task.emit(data["data"])
                        except websockets.exceptions.ConnectionClosedError:
                            await _websocket.close_connection()
                            self.webSocket_conn = None
                            self.manager.disconnected.emit(self.name)
                            break

                        except asyncio.TimeoutError:
                            pass

                    await _websocket.close()

            except ConnectionRefusedError:
                self.manager.connection_error.emit(self.name)
                await asyncio.sleep(10)

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

    @pythread.threaded("asyncio")
    async def close(self):
        self.is_running = False
        await asyncio.wrap_future(self.websocket)


class ServersManager(QObject):
    connected = pyqtSignal('PyQt_PyObject')
    connection_error = pyqtSignal('PyQt_PyObject')
    disconnected = pyqtSignal('PyQt_PyObject')
    refresh = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')

    def __init__(self, name, list_wol=None):
        QObject.__init__(self)
        self.list_wol = list_wol
        if not list_wol:
            self.list_wol = []
        self.servers_list = []
        self.loop = None
        self.name = name
        self.proto = self.run().result()
        self.send_wol()

    def send_wol(self):
        for ethernet in self.list_wol:
            send_magic_packet(ethernet)

    def new(self, name, address, **kwargs):
        self.servers_list.append(Server(self, address, name, **kwargs))

    def server(self, name):
        for server in self.servers_list:
            if server.name == name:
                return server

    def server_exist(self, name):
        for server in self.servers_list:
            if server.name == name:
                return True
        return False

    def all(self, connected=False):
        for server in self.servers_list:
            if server.webSocket_conn or not connected:
                yield server

    def close(self):
        futures = []
        for server in self.servers_list:
            print("close", server.name)
            futures.append(server.close())

        for future in futures:
            future.result()

    @pythread.threaded("asyncio")
    async def run(self):
        self.loop = asyncio.get_event_loop()
        coro = create_multicast_server(self.loop, self.name, self.on_notify)
        return self.loop.create_task(coro)

    @pythread.threaded("asyncio")
    async def find_peer(self):
        self.proto.send_who()

    def on_notify(self, name, addr):
        if not self.server_exist(name) and not name[:6] == "client":
            self.new(name, addr)
            print("new ", addr, name)
