import requests
from PyQt5.QtCore import pyqtSignal

from common_lib.fct import convert_size, convert_bit_stream, add_px, convert_duration, convert_media_type
from mediaCenter_lib.base_model import ModelTableListDict, ServerStateHandler
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

        ServerStateHandler.__init__(self, servers)
        self.refresh()

    def on_connection(self, server_name):
        self.refresh()

    def on_disconnection(self, server_name):
        self.refresh()

    def on_refresh(self, server_name, section):
        self.refresh()

    @threaded("httpCom")
    def refresh(self):
        data = []
        for server in self.servers.all():
            data += list(server.get_videos(columns=list(self.get_keys())))

        self.reset_data(data)
        self.end_refreshed()

    @threaded("httpCom")
    def delete(self, video):
        self.servers.server(video["server"]).delete_video(video["video_id"])

    @threaded("httpCom")
    def edit_movie(self, video, movie_id):
        self.servers.server(video["server"]).edit_movie(video["video_id"], movie_id)

    @threaded("httpCom")
    def edit_tv(self, video, tv_id, season, episode):
        self.servers.server(video["server"]).edit_tv(video["video_id"], tv_id, season, episode)

