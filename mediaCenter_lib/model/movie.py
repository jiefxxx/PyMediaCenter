from common_lib.config import MEDIA_TYPE_MOVIE
from common_lib.fct import convert_size, convert_duration, convert_x
from mediaCenter_lib.model import ServerStateHandler, ModelTableListDict
from pythread import threaded


class MovieModel(ServerStateHandler, ModelTableListDict):

    def __init__(self, servers, **kwargs):
        ModelTableListDict.__init__(self, [("", "last_time", False, convert_x),
                                           ("Server", "server", False, None),
                                           ("Video ID", "video_id", False, None),
                                           ("Duration", "duration", False, convert_duration),
                                           ("Size", "size", False, convert_size)], **kwargs)

        self.media_type = MEDIA_TYPE_MOVIE
        self.media_id = -1

        ServerStateHandler.__init__(self, servers)
        self.refresh()

    def on_connection(self, server_name):
        self.refresh()

    def on_disconnection(self, server_name):
        self.refresh()

    def on_refresh(self, server_name, section):
        self.refresh()

    def set_media_id(self, media_id):
        self.media_id = media_id
        self.refresh()

    @threaded("httpCom")
    def refresh(self):
        data = []
        columns = list(self.get_keys())
        columns.remove("server")
        for server in self.servers.all():
            data += list(server.get_videos(columns=columns,
                                           media_id=self.media_id,
                                           media_type=self.media_type))
        self.reset_data(data)
        self.end_refreshed()

