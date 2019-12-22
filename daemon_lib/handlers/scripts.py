from common_lib.config import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV
from pynet.http.handler import HTTPHandler
from pynet.http.tools import HTTP_CONNECTION_CONTINUE
from pynet.http.websocket import webSocket_process_key, WebSocketClient


class ScriptHandler(HTTPHandler):
    def prepare(self):
        key = self.header.get_webSocket_upgrade()

        if key is not None:     # if webSocket upgrade is true
            key = webSocket_process_key(key)
            self.upgrade(WebSocketClient(self.header, self.connection, self.get_webSocket_room()))
            return self.response.upgrade_webSocket(key)

        return HTTP_CONNECTION_CONTINUE

    def GET(self, url, script_name):
        tasks = self.user_data["tasks"]
        db = self.user_data["database"]
        if script_name is None:
            return self.response.send_error(404)

        elif script_name == "state":
            return self.response.send_json(200, tasks.json())

        elif script_name == "reset_movies":
            db.reset_table("movies")
            db.delete_column("videos", "media_id", {"media_type": MEDIA_TYPE_MOVIE})
            return self.response.send_json(200, "ok")

        elif script_name == "reset_tvs":
            db.reset_table("tv_shows")
            db.reset_table("tv_episodes")
            db.delete_column("videos", "media_id", {"media_type": MEDIA_TYPE_TV})
            return self.response.send_json(200, "ok")

        elif script_name == "reset_database":
            db.reset_table("videos")
            db.reset_table("genres")
            db.reset_table("movies")
            db.reset_table("tv_shows")
            db.reset_table("tv_episodes")
            return self.response.send_json(200, "ok")

        else:
            tasks.new_task(script_name, db)
            return self.response.send_text(200, "ok")