import os

from pynet.http.handler import HTTPHandler


class SystemHandler(HTTPHandler):
    def GET(self, url, action):
        if action == "suspend":
            os.system("systemctl suspend")
            return self.response.send_text(200, "ok")
        self.response.send_error(404)
