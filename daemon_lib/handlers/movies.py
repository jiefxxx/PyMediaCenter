from pynet.http.exceptions import HTTPError
from pynet.http.handler import HTTPHandler


class MovieHandler(HTTPHandler):

    def GET(self, url):
        movie_id = url.regex[0]
        db = self.user_data["database"]
        columns = url.get("columns")
        if columns is not None:
            columns = columns.split(",")
        if movie_id is None:
            return self.response.json(200, list(db.get("movies",
                                        columns=columns,
                                        where=url.to_sql_where(blacklist=["columns"]))))

        movies = list(db.get("movies", where={'id': int(movie_id)}))

        if len(movies) > 0:
            return self.response.json(200, movies)

        raise HTTPError(404)