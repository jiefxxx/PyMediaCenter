from pynet.http.handler import HTTPHandler


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