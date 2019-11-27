import requests
from PyQt5.QtCore import pyqtSignal

from mediaCenter_lib.base_model import ModelTableListDict
from pythread import threaded


class VideoModel(ModelTableListDict):
    refreshed = pyqtSignal()
    info = pyqtSignal('PyQt_PyObject')

    def __init__(self, **kwargs):
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

        self.refresh()

    @threaded("httpCom")
    def refresh(self):
        requested_key = ""
        for key in self.get_keys():
            requested_key += key + ","
        requested_key = requested_key[:-1]
        response = requests.get('http://192.168.1.55:4242/video?columns=' + requested_key)
        if response.status_code == 200:
            data = response.json()
            self.reset_data(data)
        self.refreshed.emit()

    @threaded("httpCom")
    def delete(self, video_id):
        response = requests.get("http://192.168.1.55:4242/video/"+str(video_id)+"/delete")
        if response.status_code == 200:
            self.refresh()
        else:
            print(response)

    @threaded("httpCom")
    def edit(self, video_id, media_type, media_id):
        response = requests.get("http://192.168.1.55:4242/video/" + str(video_id) +
                                "/edit?media_type=" + str(media_type) +
                                "&media_id=" + str(media_id))
        if response.status_code == 200:
            self.refresh()
        else:
            print(response)

