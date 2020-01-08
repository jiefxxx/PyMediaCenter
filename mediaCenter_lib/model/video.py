import requests
from PyQt5.QtCore import pyqtSignal

from common_lib.config import MEDIA_TYPE_UNKNOWN
from common_lib.fct import convert_size, convert_bit_stream, add_px, convert_duration, convert_media_type
from mediaCenter_lib.model import ServerStateHandler, ModelTableListDict
from pythread import threaded


class VideoModel( ServerStateHandler, ModelTableListDict):
    info = pyqtSignal('PyQt_PyObject')

    def __init__(self, servers, **kwargs):
        ModelTableListDict.__init__(self, [("Video ID", "video_id", False, None),
                                           ("Path", "path", False, None),
                                           ("Media Type", "media_type", False, convert_media_type),
                                           ("Media ID", "media_id", False, None),
                                           ("Duration", "duration", False, convert_duration),
                                           ("Bit Rate", "bit_rate", False, convert_bit_stream),
                                           ("Size", "size", False, convert_size),
                                           ("Codec", "codecs_video", False, None),
                                           ("Width", "width", False, add_px),
                                           ("Height", "height", False, add_px),
                                           ("Creation date", "m_time", False, None),
                                           ("Junk", "junk", False, None),
                                           ("Last", "last_time", False, None)], **kwargs)

        self.media_type = MEDIA_TYPE_UNKNOWN
        self.server_name = ""

        ServerStateHandler.__init__(self, servers)
        self.refresh()

    def on_connection(self, server_name):
        self.refresh()

    def on_disconnection(self, server_name):
        self.refresh()

    def on_refresh(self, server_name, section):
        self.refresh()

    def set_type(self, media_type):
        self.media_type = media_type
        self.refresh()

    def set_server(self, server_name):
        self.server_name = server_name
        self.refresh()

    @threaded("httpCom")
    def refresh(self):
        data = []
        if len(self.server_name) > 0:
            data += list(self.servers.server(self.server_name).get_videos(columns=list(self.get_keys()),
                                                                          media_type=self.media_type))

        self.reset_data(data)
        self.end_refreshed()

    @threaded("httpCom")
    def delete(self, video):
        self.servers.server(video["server"]).delete_video(video["video_id"])

    @threaded("httpCom")
    def edit_movie(self, video, movie_id, copy=False):
        self.servers.server(video["server"]).edit_movie(video["video_id"], movie_id, copy=copy)

    @threaded("httpCom")
    def edit_tv(self, video, tv_id, season, episode, copy=False):
        self.servers.server(video["server"]).edit_tv(video["video_id"], tv_id, season, episode, copy=copy)

    def get_video(self, video):
        return list(self.servers.server(video["server"]).get_videos(video_id=video["video_id"]))[0]

    def get_uri(self, video):
        return self.servers.server(video["server"]).get_stream(video["video_id"])

    @threaded("httpCom")
    def update_last_time(self, video):
        return self.servers.server(video["server"]).edit_last_time(video["video_id"], video["last_time"])


