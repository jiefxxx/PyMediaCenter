from pynet.http.exceptions import HTTPError
from pynet.http.handler import HTTPHandler


class VideoInfoHandler(HTTPHandler):
    compression = "gzip"

    def GET(self, url):
        video_id = url.get("video_id", data_type=int)
        db = self.user_data["database"]
        columns = url.get("columns")
        if columns:
            columns = columns.split(",")
        if not video_id:

            return self.response.json(200, list(db.get("videos", columns=columns,
                                                       where=url.to_sql_where(blacklist=["columns"]))))

        videos = list(db.get("videos", columns=columns, where={'video_id': video_id}))
        if len(videos) > 0:
            return self.response.json(200, videos)

        raise HTTPError(404)


class MovieHandler(HTTPHandler):
    compression = "gzip"

    def GET(self, url):
        movie_id = url.get("id", data_type=int)
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


class TvShowHandler(HTTPHandler):
    compression = "gzip"

    def GET(self, url):
        tv_id = url.get("id", data_type=int)
        db = self.user_data["database"]
        columns = url.get("columns")

        if columns is not None:
            columns = columns.split(",")
        if tv_id is None:
            return self.response.json(200, list(db.get("tv_shows",
                                                columns=columns,
                                                where=url.to_sql_where(blacklist=["columns"]))))

        tvs = list(db.get("tv_shows", where={'id': int(tv_id)}))

        if len(tvs) > 0:
            return self.response.json(200, tvs)

        raise HTTPError(404)


class TvEpisodeHandler(HTTPHandler):
    compression = "gzip"

    def GET(self, url):
        episode_id = url.get("id", data_type=int)
        db = self.user_data["database"]
        columns = url.get("columns")
        if columns is not None:
            columns = columns.split(",")
        if episode_id is None:
            return self.response.json(200, list(db.get("tv_episodes",
                                                columns=columns,
                                                where=url.to_sql_where(blacklist=["columns"]))))

        episodes = list(db.get("tv_episodes", where={'id': int(episode_id)}))

        if len(episodes) > 0:
            return self.response.json(200, episodes)

        raise HTTPError(404)