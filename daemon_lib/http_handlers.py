from common_lib.config import MEDIA_TYPE_MOVIE
from common_lib.videos_info import get_video_info, get_movie_info, get_normalized_file_name, check_for_space
from pynet.http_server import HTTP_handler


class UploadHandler(HTTP_handler):
    def GET(self, url, **kwargs):
        self.send_text(200, "test ok")

    def POST(self, url, db, cm, **kwargs):
        multipart_file = self.request.data.get_multipart()
        json_data = multipart_file.get("data").json()
        video_data = multipart_file.get("video")
        video_info = get_video_info(video_data.file.name, json_data["media_type"])
        video_info["media_id"] = json_data["media_id"]
        ext = video_data.filename.split('.')[-1]
        size = video_data.size
        if video_info["media_type"] == MEDIA_TYPE_MOVIE:
            base_paths = cm.get("videos.movies.path")
            movie_info = get_movie_info(video_info["media_id"])
            filename = get_normalized_file_name(movie_info, ext)
            for path in base_paths:
                if check_for_space(path, size):
                    video_info["path"] = path+"/"+filename
                    movie_info["genre_ids"] = []
                    for genre in movie_info["genres"]:
                        movie_info["genre_ids"].append(genre["id"])
                    video_data.save_as(video_info["path"])
                    db.set("videos", video_info)
                    db.set("movies", movie_info)
                    self.send_text(200, "ok "+video_info["path"])
                    return

        self.send_error(400)


class MovieHandler(HTTP_handler):

    def GET(self, url, movie_id, db, cm):
        genre_dict = self._create_genre_dict(db.get("genres"))
        columns = url.get("columns")
        if columns is not None:
            columns = columns.split(",")
        if movie_id is None:
            return self.send_json(200, self._adding_genre(genre_dict, list(db.get("movies",
                                        columns=columns,
                                        where=url.to_sql_where(blacklist=["columns"])))))

        movies = self._adding_genre(genre_dict, list(db.get("movies", where={'id': int(movie_id)})))

        if len(movies) > 0:
            return self.send_json(200, movies)

        return self.send_error(404)

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


class GenreHandler(HTTP_handler):
    def GET(self, url, db, cm):
        self.send_json(200, list(db.get("genres")))


class VideoHandler(HTTP_handler):
    def GET(self, url, video_id, action, db, cm):

        columns = url.get("columns")
        if columns is not None:
            columns = columns.split(",")

        if video_id is None:
            return self.send_json(200, list(db.get("videos", columns=columns,
                                        where=url.to_sql_where(blacklist=["columns"]))))
        else:
            videos = list(db.get("videos", columns=columns, where={'video_id': int(video_id)}))

        if len(videos) == 0:
            return self.send_error(404)

        if action is None:
            return self.send_json(200, videos[0])

        if action == "stream":
            try:
                return self.send_file(videos[0]["path"])
            except FileNotFoundError:
                pass

        return self.send_error(404)
