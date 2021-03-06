import time

from common_lib.config import NOTIFY_REFRESH, NOTIFY_TASK
from pynet.http.websocket import WebSocketRoom


class ScriptsRoom(WebSocketRoom):
    def __init__(self, name=None):
        WebSocketRoom.__init__(self, name)
        self.last_time = time.time()

    def on_new(self, client):
        print("new client", client)

    def on_message(self, client, message):
        print(client, message)

    def on_close(self, client):
        print("close client", client)

    def notify_refresh(self, section):
        self.notify(NOTIFY_REFRESH, section)

    def notify_task(self, task):
        self.notify(NOTIFY_TASK, task)

    def notify(self, notify_id, data):
        self.send_json({"id": notify_id,
                        "data": data})
