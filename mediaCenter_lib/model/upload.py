import json
import os
import time

import requests
from PyQt5.QtWidgets import QFileDialog
from requests_toolbelt import MultipartEncoderMonitor

from common_lib.config import MEDIA_TYPE_MOVIE
from common_lib.fct import convert_size
from mediaCenter_lib.base_model import ModelTableListDict
from pythread import threaded


class UploadVideoModel(ModelTableListDict):
    def __init__(self):
        ModelTableListDict.__init__(self, [("Path", "path", False),
                                           ("Size", "size", False),
                                           ("Edited", "edited", False),
                                           ("Status", "status", False)], None)

    def add(self, files=None):
        if files is None:
            files, _ = QFileDialog.getOpenFileNames(None, "get videos", "",
                                                    "Video files (*.asf *.avi *.flv *.m4v *.mkv *.mov *.mp4 *.mpg "
                                                    "*.mpeg)")
        for file in files:
            video, _ = self.get_by_path(file)
            if video is None:
                self.add_data({"path": file, "size": convert_size(os.path.getsize(file))})

    def get_by_path(self, path):
        for i in range(0, len(self.list)):
            if self.list[i]["path"] == path:
                return self.list[i], self.createIndex(i, 0)
        return None, None

    def set_info(self, index, info):
        video = self.data(index)
        video["id"] = info["id"]
        video["media_type"] = MEDIA_TYPE_MOVIE
        video["edited"] = "find movie : " + info["title"] + " " + info["release_date"][:4]
        self.setData(index, video)

    def _status(self, path, status):
        video, index = self.get_by_path(path)
        if video is None:
            return
        video["status"] = status
        self.setData(index, video)

    def send(self, index):
        self._status(index, "Queued")
        self.threaded_send(index)

    @threaded("upload")
    def threaded_send(self, index):
        self.begin_busy()
        video = self.data(index)
        path = video.get("path")
        media_type = video.get("media_type")
        media_id = video.get("id")
        if path and media_type and media_id:

            def callback(monitor):
                try:
                    elapsed = time.time()-callback.first_time
                    bandwidth = round((monitor.bytes_read / elapsed)/(1024*1024), 2)
                except AttributeError:
                    callback.first_time = time.time()
                    bandwidth = 0

                progress = round(monitor.bytes_read/monitor.len*100.0, 2)
                if monitor.bytes_read == monitor.len:
                    self._status(path, "writing file to disk...")
                else:
                    self._status(path, "Sending... ("+str(progress)+"): "+str(bandwidth)+"MB/S")

            m = MultipartEncoderMonitor.from_fields(
                fields={"json": json.dumps({"media_id": media_id,
                                            "ext": path.split(".")[-1]}),
                        'video': open(path, 'rb')},
                callback=callback
            )

            self._status(path, "Sending...")
            try:
                r = requests.post("http://192.168.1.55:4242/upload?media_type="+str(media_type), data=m,
                                  headers={'Content-Type': m.content_type})
                if r.status_code == 200:
                    self._status(path, "Send completed")
                else:
                    self._status(path, "Send error")
            except requests.exceptions.ConnectionError:
                self._status(path, "Send connection error")
        else:
            self._status(path, "Invalid data")
        self.end_busy()