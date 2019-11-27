import json
import os
import time

import requests
from PyQt5.QtWidgets import QFileDialog
from requests_toolbelt import MultipartEncoderMonitor

from common_lib.config import MEDIA_TYPE_MOVIE
from common_lib.fct import convert_size
from mediaCenter_lib.base_model import ModelTableListDict
from pythread import threaded, create_new_mode
from pythread.modes import RunForeverMode


class UploadVideoModel(ModelTableListDict):
    def __init__(self, **kwargs):
        ModelTableListDict.__init__(self, [("Type", "type", False),
                                           ("Path", "path", False),
                                           ("Size", "size", False),
                                           ("Edited", "edited", False),
                                           ("Status", "status", False)], **kwargs)
        create_new_mode(RunForeverMode, "up.down", self.run_video_transfer)

    def add_upload(self, files=None):
        if files is None:
            files, _ = QFileDialog.getOpenFileNames(None, "get videos", "",
                                                    "Video files (*.asf *.avi *.flv *.m4v *.mkv *.mov *.mp4 *.mpg "
                                                    "*.mpeg)")
        for file in files:
            video, _ = self.get_by_path(file)
            if video is None:
                self.add_data({"type": "upload",
                               "path": file,
                               "size": convert_size(os.path.getsize(file)),
                               "status": "pending"})

    def add_download(self, video_id, location):
        response = requests.get('http://192.168.1.55:4242/video/' + str(video_id))
        data = None
        if response.status_code == 200:
            data = response.json()

        if not data:
            raise Exception("video data not found (" + str(video_id) + ")")

        filename = os.path.basename(data["path"])

        filename = location + "/" + filename

        self.add_data({"type": "download",
                       "video_id": video_id,
                       "path": filename,
                       "size": convert_size(data["size"]),
                       "status": "queued"})

    def get_by_path(self, path):
        for i in range(0, len(self.list)):
            if self.list[i]["path"] == path:
                return self.list[i], self.createIndex(i, 0)
        return None, None

    def set_info(self, index, info):
        video = self.data(index)
        if video["type"] == "upload":
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
        video = self.data(index)
        video["status"] = "queued"
        self.setData(index, video)

    def run_video_transfer(self):
        for video in self.list:
            if video["status"] == "queued":
                if video["type"] == "download":
                    self.download_video(video)
                elif video["type"] == "upload":
                    self.upload_video(video)
        time.sleep(1)
        return True

    def download_video(self, video):
        video_id = video["video_id"]
        filename = video["path"]
        first_time = time.time()
        with requests.get('http://192.168.1.55:4242/video/' + str(video_id) + "/stream", stream=True) as r:
            if r.status_code == 200:
                size = int(r.headers['Content-length'])
                cur_size = 0
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive new chunks
                            cur_size += len(chunk)
                            f.write(chunk)
                            # f.flush()
                            brandwith = cur_size/(time.time() - first_time)
                            self._status(filename, "download " + str(int((cur_size/size)*100)) + "% " +
                                         convert_size(brandwith) + "/s")
                self._status(filename, "ended")
            else:
                self._status(filename, "error downloading")

    def upload_video(self, video):
        self.begin_busy()
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
