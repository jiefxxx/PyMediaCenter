import json
import os
import time

import requests
from PyQt5.QtWidgets import QFileDialog
from requests_toolbelt import MultipartEncoderMonitor

from common_lib.config import MEDIA_TYPE_MOVIE
from common_lib.fct import convert_size
from mediaCenter_lib.model import ModelTableListDict
from pythread import threaded, create_new_mode
from pythread.modes import RunForeverMode


class FileSharingModel(ModelTableListDict):
    def __init__(self, servers, **kwargs):
        ModelTableListDict.__init__(self, [("Type", "type", False, None),
                                           ("Path", "path", False, None),
                                           ("Size", "size", False, None),
                                           ("Edited", "edited", False, None),
                                           ("Server", "server", False, None),
                                           ("Status", "status", False, None)], **kwargs)
        self.servers = servers
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

    def add_download(self, video, location):
        data = list(self.servers.server(video["server"]).get_videos(video_id=video["video_id"]))[0]

        filename = os.path.basename(data["path"])

        filename = location + "/" + filename

        self.add_data({"type": "download",
                       "server": data["server"],
                       "video_id": data["video_id"],
                       "path": filename,
                       "size": convert_size(data["size"]),
                       "status": "queued"})

    def update_video_set(self, videos):
        for video in videos:
            model_video, index = self.get_by_path(video["path"])
            model_video.update(video)
            model_video["edited"] = "find tv :"+model_video["name"]+" S" +\
                                    str(model_video["season_number"])+"E" +\
                                    str(model_video["episode_number"])
            model_video["id"] = (model_video["tv_id"], model_video["season_number"], model_video["episode_number"])
            self.setData(index, model_video)

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

    def _status(self, path, status, progress):
        video, index = self.get_by_path(path)
        if video is None:
            return
        video["status"] = status
        self.setData(index, video)

    def send(self, index, server_name):
        video = self.data(index)
        video["status"] = "queued"
        video["server"] = server_name
        self.setData(index, video)

    def run_video_transfer(self):
        for video in self.list:
            if video["status"] == "queued":
                if video["type"] == "download":
                    self.begin_busy()
                    self.servers.server(video["server"]).download_video(video.get("video_id"),
                                                                        video.get("path"), callback=self._status)
                    self.end_busy()
                elif video["type"] == "upload":
                    self.begin_busy()
                    self.servers.server(video["server"]).upload_video(video.get("path"),
                                                                      video.get("media_type"),
                                                                      video.get("id"), callback=self._status)
                    self.end_busy()
        time.sleep(1)
        return True

    def get_servers(self):
        ret = []
        for server in self.servers.all():
            ret.append(server.name)
        return ret
