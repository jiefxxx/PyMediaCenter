from pynet.http.websocket import WebSocketRoom


class ScriptsRoom(WebSocketRoom):
    def on_new(self, client):
        print("new client", client)

    def on_message(self, client, message):
        print(client, message)
