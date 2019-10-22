from pynet.http_server import HTTP_handler
from pynet.http_tools import sql_where_from_url


class MovieHandler(HTTP_handler):

    def GET(self, url, movie_id, db, cm):
        genre_dict = self._create_genre_dict(db.get("genres"))

        if movie_id is None:
            return self.send_json(200, self._adding_genre(genre_dict, list(db.get("movies",
                                        columns=["video_id", "title", "genre_ids", "original_title", "duration",
                                                 "release_date", "vote_average", "poster_path", "id"],
                                        where=sql_where_from_url(url)))))

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
        if video_id is None:
            return self.send_json(200, list(db.get("videos", where=sql_where_from_url(url))))

        videos = list(db.get("videos", where={'video_id': int(video_id)}))

        if action is None and len(videos) > 0:
            return self.send_json(200, videos[0])

        if action == "stream":
            try:
                return self.send_file(videos[0]["path"])
            except FileNotFoundError:
                print("file not found")

        return self.send_error(404)
