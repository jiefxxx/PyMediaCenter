from pynet.http_server import HTTP_handler
from pynet.http_tools import sql_where_from_url


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
