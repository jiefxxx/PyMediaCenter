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
        scripts = self.user_data["scripts"]
        db = self.user_data["database"]
        if script_name is None:
            return self.response.send_error(404)

        if script_name == "state":
            return self.response.send_json(200, scripts.get_state())

        if scripts.start_script(script_name, db):
            return self.response.send_text(200, "ok")

        return self.response.send_error(404)