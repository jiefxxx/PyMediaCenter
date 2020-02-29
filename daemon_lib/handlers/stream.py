import json
import os
import time

from pynet.http.exceptions import HTTPError
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import FileTarget, ValueTarget

import pyconfig
from common_lib.config import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_UNKNOWN
from common_lib.fct import ensure_dir
from common_lib.videos_info import check_for_space, get_movie_info, get_normalized_file_name, get_video_info, \
    get_tv_info, get_episode_info, get_normalized_episode_name
from pynet.http.handler import HTTPHandler
from pynet.http import HTTP_CONNECTION_CONTINUE


class StreamHandler(HTTPHandler):
    enable_range = True

    async def prepare(self):
        ret = await HTTPHandler.prepare(self)
        if self.header.query == "POST":
            base_paths = []
            self.user_data["media_type"] = int(self.header.url.get("media_type", default=0))
            approximated_size = int(self.header.fields.get("Content-Length", default=0))
            if self.user_data["media_type"] == MEDIA_TYPE_MOVIE:
                base_paths = pyconfig.get("videos.movies.path")

            elif self.user_data["media_type"] == MEDIA_TYPE_TV:
                base_paths = pyconfig.get("videos.tvs.path")

            elif self.user_data["media_type"] == MEDIA_TYPE_UNKNOWN:
                base_paths = pyconfig.get("videos.downloads.path")

            for path in base_paths:

                if check_for_space(path, approximated_size):
                    self.data = StreamingFormDataParser(headers={'Content-Type': self.header.fields.get("Content-Type")})
                    self.user_data["file"] = FileTarget(path+"/temporary."+str(time.time())+".video")
                    self.user_data["json"] = ValueTarget()
                    self.data.register('video', self.user_data["file"])
                    self.data.register('json', self.user_data["json"])
                    return HTTP_CONNECTION_CONTINUE
            raise Exception("No space available in path :"+str(base_paths))
        return ret

    def write(self, data_chunk):
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

            movie_info = get_movie_info(media_id, language=pyconfig.get("language"))

            definitive_filename = os.path.dirname(temporary_filename) + "/" + get_normalized_file_name(movie_info, ext)
            os.rename(temporary_filename, definitive_filename)

            video_info = get_video_info(definitive_filename, media_type)
            video_info["media_id"] = movie_info["id"]
            db.set("videos", video_info)
            db.set("movies", movie_info)
            self.response.text(200, "ok " + video_info["path"])
            self.user_data["notify"].notify_refresh("movies")
            return

        elif media_type == MEDIA_TYPE_TV:
            tv_id = media_id[0]
            season = media_id[1]
            episode = media_id[2]
            tv_info = get_tv_info(tv_id, language=pyconfig.get("language"))
            episode_info = get_episode_info(tv_id, season, episode, language=pyconfig.get("language"))
            definitive_filename = os.path.dirname(temporary_filename)+"/"+get_normalized_episode_name(tv_info,
                                                                                                      season,
                                                                                                      episode,
                                                                                                      ext)

            ensure_dir(os.path.dirname(definitive_filename))
            os.rename(temporary_filename, definitive_filename)

            video_info = get_video_info(definitive_filename, media_type)
            video_info["media_id"] = episode_info["id"]

            db.set("tv_shows", tv_info)
            db.set("tv_episodes", episode_info)
            db.set("videos", video_info)

            self.response.text(200, "ok " + video_info["path"])
            self.user_data["notify"].notify_refresh("tvs")
            return

        elif media_type == MEDIA_TYPE_UNKNOWN:
            definitive_filename = os.path.dirname(temporary_filename) + "/" + json_data["filename"]
            ensure_dir(os.path.dirname(definitive_filename))
            os.rename(temporary_filename, definitive_filename)

            video_info = get_video_info(definitive_filename, MEDIA_TYPE_UNKNOWN)

            db.set("videos", video_info)
            self.user_data["notify"].notify_refresh("tvs")

        raise HTTPError(400)

    def GET(self, url):
        video_id = url.get("video_id", data_type=int)
        db = self.user_data["database"]
        videos = list(db.get("videos", where={'video_id': video_id}))
        if len(videos) > 0:
            return self.file(videos[0]["path"])

        raise HTTPError(404)

