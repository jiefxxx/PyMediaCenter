from pynet.http.handler import HTTPHandler


class GenreHandler(HTTPHandler):
    def GET(self, url):
        db = self.user_data["database"]
        self.response.json(200, list(db.get("genres")))