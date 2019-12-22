from pynet.http.handler import HTTPHandler


class TvShowHandler(HTTPHandler):

    def GET(self, url, tv_id):
        db = self.user_data["database"]
        columns = url.get("columns")
        if columns is not None:
            columns = columns.split(",")
        if tv_id is None:
            return self.response.send_json(200, list(db.get("tv_shows",
                                                columns=columns,
                                                where=url.to_sql_where(blacklist=["columns"]))))

        tvs = list(db.get("tv_shows", where={'id': int(tv_id)}))

        if len(tvs) > 0:
            return self.response.send_json(200, tvs)

        return self.response.send_error(404)


class TvEpisodeHandler(HTTPHandler):

    def GET(self, url, episode_id):
        db = self.user_data["database"]
        columns = url.get("columns")
        if columns is not None:
            columns = columns.split(",")
        if episode_id is None:
            return self.response.send_json(200, list(db.get("tv_episodes",
                                                columns=columns,
                                                where=url.to_sql_where(blacklist=["columns"]))))

        episodes = list(db.get("tv_episodes", where={'id': int(episode_id)}))

        if len(episodes) > 0:
            return self.response.send_json(200, episodes)

        return self.response.send_error(404)
