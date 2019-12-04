from common_lib.config import NOTIFY_REFRESH, NOTIFY_PROGRESS
from pynet.http.websocket import WebSocketRoom

class ScriptsRoom(WebSocketRoom):
    def on_new(self, client):
        print("new client", client)

    def on_message(self, client, message):
        print(client, message)

    def notify_refresh(self, section):
        self.notify(NOTIFY_REFRESH, section)

    def notify_progress(self, progress):
        self.notify(NOTIFY_PROGRESS, progress)

    def notify(self, notify_id, data):
        self.send_json({"id": notify_id,
                        "data": data})
