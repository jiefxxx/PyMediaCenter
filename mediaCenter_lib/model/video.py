import requests
from PyQt5.QtCore import pyqtSignal

from mediaCenter_lib.base_model import ModelTableListDict, ServerStateHandler
from pythread import threaded


class VideoModel( ServerStateHandler, ModelTableListDict):
    refreshed = pyqtSignal()
    info = pyqtSignal('PyQt_PyObject')

    def __init__(self, servers, **kwargs):
        ModelTableListDict.__init__(self, [("Video ID", "video_id", False),
                                           ("Path", "path", False),
                                           ("Media Type", "media_type", False),
                                           ("Media ID", "media_id", False),
                                           ("Bit Rate", "bit_rate", False),
                                           ("Codec", "codecs_video", False),
                                           ("Width", "width", False),
                                           ("Height", "height", False),
                                           ("Size", "size", False),
                                           ("Creation date", "m_time", False),
                                           ("Junk", "junk", False),
                                           ("Last", "last_time", False)], **kwargs)

        ServerStateHandler.__init__(self, servers)
        self.refresh()

    def on_connection(self, server_name):
        self.refresh()

    def on_disconnection(self, server_name):
        self.refresh()

    def on_refresh(self, server_name, section):
        if section == "video":
            self.refresh()

    @threaded("httpCom")
    def refresh(self):
        data = []
        for server in self.servers.all():
            data += list(server.get_videos(columns=list(self.get_keys())))

        self.reset_data(data)
        self.refreshed.emit()

    @threaded("httpCom")
    def delete(self, video):
        self.servers.server(video["server"]).delete_video(video["video_id"])
        self.refresh()

    @threaded("httpCom")
    def edit(self, video, media_type, media_id):
        self.serves.server(video["server"]).edit_video(video["video_id"], media_type, media_id)
        self.refresh()

