import json
import os
import time

from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import FileTarget, ValueTarget

from common_lib.config import MEDIA_TYPE_MOVIE
from common_lib.videos_info import get_video_info, get_movie_info, get_normalized_file_name, check_for_space
from pynet.http_handler import HTTPHandler
from pynet.http_tools import HTTP_CONNECTION_ABORT, HTTP_CONNECTION_CONTINUE


class UploadHandler(HTTPHandler):
    def prepare(self, headers):
        cm = self.user_data["config"]

        self.user_data["media_type"] = int(headers.url.get("media_type", default=0))
        if self.user_data["media_type"] == MEDIA_TYPE_MOVIE:
            approximated_size = int(headers.fields.get("Content-Length", default=0))
            base_paths = cm.get("videos.movies.path")
            for path in base_paths:
                if check_for_space(path, approximated_size):
                    self.data = StreamingFormDataParser(headers={'Content-Type': headers.fields.get("Content-Type")})
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


class MovieHandler(HTTPHandler):

    def GET(self, url, movie_id):
        db = self.user_data["database"]
        genre_dict = self._create_genre_dict(db.get("genres"))
        columns = url.get("columns")
        if columns is not None:
            columns = columns.split(",")
        if movie_id is None:
            return self.response.send_json(200, self._adding_genre(genre_dict, list(db.get("movies",
                                        columns=columns,
                                        where=url.to_sql_where(blacklist=["columns"])))))

        movies = self._adding_genre(genre_dict, list(db.get("movies", where={'id': int(movie_id)})))

        if len(movies) > 0:
            return self.response.send_json(200, movies)

        return self.response.send_error(404)

    @staticmethod
    def _create_genre_dict(genres):
        genre_dict = {}
        for genre in genres:
            genre_dict[genre["id"]] = genre["name"]
        return genre_dict

    @staticmethod
    def _adding_genre(genre_dict, movies):
        ret = []
        for movie in movies:
            if "genre_ids" in movie:
                movie["genres"] = []
                for genre_id in movie["genre_ids"]:
                    movie["genres"].append(genre_dict[genre_id])
                del movie["genre_ids"]
            ret.append(movie)
        return ret


class GenreHandler(HTTPHandler):
    def GET(self, url):
        db = self.user_data["database"]
        self.response.send_json(200, list(db.get("genres")))


class VideoHandler(HTTPHandler):
    def GET(self, url, video_id, action):
        db = self.user_data["database"]
        columns = url.get("columns")
        if columns is not None:
            columns = columns.split(",")

        if video_id is None:
            return self.response.send_json(200, list(db.get("videos", columns=columns,
                                        where=url.to_sql_where(blacklist=["columns"]))))
        else:
            videos = list(db.get("videos", columns=columns, where={'video_id': int(video_id)}))

        if len(videos) == 0:
            return self.response.send_error(404)

        if action is None:
            return self.response.send_json(200, videos[0])

        if action == "stream":
            try:
                return self.response.send_file(videos[0]["path"])
            except FileNotFoundError:
                pass

        return self.response.send_error(404)
