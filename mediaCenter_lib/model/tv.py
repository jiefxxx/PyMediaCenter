import textwrap

from PyQt5.QtCore import pyqtSignal, QVariant
from PyQt5.QtGui import QIcon, QPixmap

from common_lib.config import MEDIA_TYPE_TV
from common_lib.videos_info import parse_episode_path
from mediaCenter_lib.base_model import ModelTableListDict, ServerStateHandler
from mediaCenter_lib.poster_manager import PosterManager
from pythread import threaded


class TvShowModel(ServerStateHandler, PosterManager, ModelTableListDict):
    info = pyqtSignal('PyQt_PyObject')

    def __init__(self, servers,  **kwargs):
        ModelTableListDict.__init__(self, [("#", None, False, None),
                                           ("Title", "name", False, None),
                                           ("Original Title", "original_name", False, None),
                                           ("Tv ID", "id", False, None),
                                           ("Genres", "genre_name", False, None),
                                           ("Release date", "first_air_date", False, None),
                                           ("Vote", "vote_average", False, None),
                                           ("Poster", "poster_path", False, None)], **kwargs)

        PosterManager.__init__(self)

        ServerStateHandler.__init__(self, servers)
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
            data += list(server.get_tv_shows(columns=list(self.get_keys())))
        self.reset_data(data)
        self.end_refreshed()

    def get_decoration_role(self, index):
        if index.column() == 0:
            if self.poster_exists(self.list[index.row()]["poster_path"]):
                return QIcon(QPixmap(self.get_poster_path(self.list[index.row()]["poster_path"], mini=True)))
            else:
                return QIcon(QPixmap("rsc/404.jpg"))
        return QVariant()


class TvEpisodeModel(ServerStateHandler, PosterManager, ModelTableListDict):
    info = pyqtSignal('PyQt_PyObject')

    def __init__(self, servers,  **kwargs):
        ModelTableListDict.__init__(self, [("#", "tv_id", False, None),
                                           ("#", "video_id", False, None),
                                           ("S", "season_number", False, None),
                                           ("E", "episode_number", False, None),
                                           ("Title", "episode_name", False, None),
                                           ("Overview", "episode_overview", False, None)], **kwargs)

        PosterManager.__init__(self)

        ServerStateHandler.__init__(self, servers)

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
            data += list(server.get_tv_episodes(columns=list(self.get_keys())))
        self.reset_data(data)
        self.end_refreshed()

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

