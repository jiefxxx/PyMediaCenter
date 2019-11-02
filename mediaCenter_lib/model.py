import json
import os

import requests
from PyQt5.QtWidgets import QFileDialog

from common_lib.config import MEDIA_TYPE_MOVIE
from common_lib.fct import convert_size
from common_lib.videos_info import SearchMovie
from mediaCenter_lib.base_model import ModelTableListDict
from pythread.threadMananger import ThreadMananger, threadedFunction


class TmdbModel(ModelTableListDict, ThreadMananger):
    def __init__(self, api_key, parent):
        ThreadMananger.__init__(self, 1, debug=False)
        ModelTableListDict.__init__(self, [("Title", "title", False),
                                           ("Release date", "release_date", False)], parent)
        self.search = SearchMovie(api_key)

    @threadedFunction(0)
    def on_search(self, text, year=None):
        self.begin_busy()
        self.clear()
        for movie in self.search.search_movie(text, year):
            self.add_data(movie)
        self.end_busy()

    def __del__(self):
        self.close()


class UploadVideoModel(ModelTableListDict, ThreadMananger):
    def __init__(self, parent):
        ThreadMananger.__init__(self, 1, debug=False)
        ModelTableListDict.__init__(self, [("Path", "path", False),
                                           ("Size", "size", False),
                                           ("Edited", "edited", False),
                                           ("Status", "status", False)], parent)

    def add(self, files=None):
        if files is None:
            files, _ = QFileDialog.getOpenFileNames(self.parent(), "get videos", "",
                                                    "Video files (*.asf *.avi *.flv *.m4v *.mkv *.mov *.mp4 *.mpg "
                                                    "*.mpeg)")
        for file in files:
            self.add_data({"path": file, "size": convert_size(os.path.getsize(file))})

    def set_info(self, index, info):
        video = self.data(index)
        video["id"] = info["id"]
        video["media_type"] = MEDIA_TYPE_MOVIE
        video["edited"] = "find movie : " + info["title"] + " " + info["release_date"][:4]
        self.setData(index, video)

    def _status(self, index, status):
        video = self.data(index)
        video["status"] = status
        self.setData(index, video)

    def send(self, index):
        self._status(index, "Queued")
        self.threaded_send(index)

    @threadedFunction(0)
    def threaded_send(self, index):
        self.begin_busy()
        video = self.data(index)
        path = video.get("path")
        media_type = video.get("media_type")
        media_id = video.get("id")
        if path and media_type and media_id:
            send_json = {"data": json.dumps({"media_id": media_id, "media_type": media_type, "testing": True})}
            files = {'video': open(path, 'rb')}
            self._status(index, "Sending...")
            requests.post("http://192.168.1.55:4242/upload", files=files, data=send_json)
            self._status(index, "Send completed")
        else:
            self._status(index, "Invalid data")
            # raise Exception("video not ready") Not sur what to doo ///
        self.end_busy()

    def __del__(self):
        self.close()
