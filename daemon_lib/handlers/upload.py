import json
import os
import time

from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import FileTarget, ValueTarget

import pyconfig
from common_lib.config import MEDIA_TYPE_MOVIE
from common_lib.videos_info import check_for_space, get_movie_info, get_normalized_file_name, get_video_info
from pynet.http.handler import HTTPHandler
from pynet.http.tools import HTTP_CONNECTION_CONTINUE, HTTP_CONNECTION_ABORT


class UploadHandler(HTTPHandler):
    def prepare(self):
        self.user_data["media_type"] = int(self.header.url.get("media_type", default=0))
        if self.user_data["media_type"] == MEDIA_TYPE_MOVIE:
            approximated_size = int(self.header.fields.get("Content-Length", default=0))
            base_paths = pyconfig.get("videos.movies.path")
            for path in base_paths:
                if check_for_space(path, approximated_size):
                    self.data = StreamingFormDataParser(headers={'Content-Type': self.header.fields.get("Content-Type")})
                    self.user_data["file"] = FileTarget(path+"/temporary."+str(time.time())+".movie")
                    self.user_data["json"] = ValueTarget()
                    self.data.register('video', self.user_data["file"])
                    self.data.register('json', self.user_data["json"])
                    return HTTP_CONNECTION_CONTINUE
            raise Exception("No space available in path :"+str(base_paths))
        return HTTP_CONNECTION_ABORT

    def feed(self, data_chunk):
        self.data.data_received(data_chunk)

    def POST(self, url):
        print("process data", self.user_data["json"].value)

        db = self.user_data["database"]
        json_data = json.loads(self.user_data["json"].value)
        temporary_filename = self.user_data["file"].filename

        media_type = self.user_data["media_type"]
        media_id = json_data["media_id"]
        ext = json_data["ext"]

        if media_type == MEDIA_TYPE_MOVIE:

            movie_info = get_movie_info(media_id)
            movie_info["genre_ids"] = []
            for genre in movie_info["genres"]:
                movie_info["genre_ids"].append(genre["id"])

            definitive_filename = os.path.dirname(temporary_filename) + "/" + get_normalized_file_name(movie_info, ext)
            os.rename(temporary_filename, definitive_filename)

            video_info = get_video_info(definitive_filename, media_type)
            video_info["media_id"] = movie_info["id"]
            db.set("videos", video_info)
            db.set("movies", movie_info)
            self.response.send_text(200, "ok " + video_info["path"])
            return

        print("media_type "+str(media_type))
        self.response.send_error(400)