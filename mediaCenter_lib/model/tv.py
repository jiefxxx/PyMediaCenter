import textwrap

from PyQt5.QtCore import pyqtSignal, QSortFilterProxyModel, Qt

from common_lib.config import MEDIA_TYPE_TV
from common_lib.fct import convert_x
from common_lib.videos_info import parse_episode_path
from mediaCenter_lib.model import ServerStateHandler, ModelTableListDict, PosterManager
from pythread import threaded


class TvEpisodeModel(ServerStateHandler, PosterManager, ModelTableListDict):
    info = pyqtSignal('PyQt_PyObject')

    def __init__(self, servers,  **kwargs):
        ModelTableListDict.__init__(self, [("", "last_time", False, convert_x),
                                           ("#", "video_id", False, None),
                                           ("S", "season_number", False, None),
                                           ("E", "episode_number", False, None),
                                           ("Title", "episode_name", False, None),
                                           ("Overview", "episode_overview", False, None)], **kwargs)

        PosterManager.__init__(self)

        ServerStateHandler.__init__(self, servers)

        self.tv_id = -1

        self.refresh()

    def on_connection(self, server_name):
        self.refresh()

    def on_disconnection(self, server_name):
        self.refresh()

    def on_refresh(self, server_name, section):
        if section == "tvs":
            self.refresh()

    @threaded("httpCom")
    def refresh(self):
        data = []
        for server in self.servers.all():
            data += list(server.get_tv_episodes(columns=list(self.get_keys()), tv_id=self.tv_id))
        self.reset_data(data)
        self.end_refreshed()

    def get_proxy(self):
        proxy = SortEpisode()
        proxy.setSourceModel(self)
        return proxy

    def set_tv_id(self, tv_id):
        self.tv_id = tv_id
        self.refresh()

    def get_toolTip_role(self, index):
        return textwrap.fill(self.list[index.row()]["episode_overview"], width=70)


class TvMakerModel(ModelTableListDict):
    def __init__(self, videos, tv_show, **kwargs):
        self.tv_show = tv_show
        ModelTableListDict.__init__(self, [("Path", "path", False, None),
                                           ("S", "season_number", True, None),
                                           ("E", "episode_number", True, None),
                                           ("Validate", "validate", False, None)], **kwargs)
        _list = []
        for video in videos:
            el = {"name": tv_show["name"],
                  "path": video["path"],
                  "tv_id": tv_show["id"],
                  "media_type": MEDIA_TYPE_TV,
                  "video": video,
                  "season_number": parse_episode_path(video["path"])[0],
                  "episode_number": parse_episode_path(video["path"])[1]}
            _list.append(el)

        self.reset_data(_list)

    def set_season(self, season):
        for el in self.list:
            el["season_number"] = int(season)
        self.reset_data(self.list)


class SortEpisode(QSortFilterProxyModel):
    def __init__(self):
        QSortFilterProxyModel.__init__(self, None)
        self.tv_id = 0
        self.reverse = False

    def lessThan(self, left, right):
        left_data = self.sourceModel().data(left)
        right_data = self.sourceModel().data(right)
        if left_data["season_number"] < right_data["season_number"]:
            return True
        elif left_data["season_number"] == right_data["season_number"]:
            return left_data["episode_number"] < right_data["episode_number"]
        else:
            return False

    def do_sort(self):
        if self.reverse:
            self.sort(0, order=Qt.DescendingOrder)
        else:
            self.sort(0, order=Qt.AscendingOrder)
        self.invalidate()