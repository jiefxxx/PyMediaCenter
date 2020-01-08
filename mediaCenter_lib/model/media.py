from PyQt5.QtCore import pyqtSignal, QVariant, QSortFilterProxyModel, Qt
from PyQt5.QtGui import QIcon, QPixmap

from common_lib.config import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV
from common_lib.fct import filter_by_string
from mediaCenter_lib.model import ServerStateHandler, ModelTableListDict, PosterManager
from mediaCenter_lib.model.genre import GenreModel
from pythread import threaded


class MediaModel(ServerStateHandler, PosterManager, ModelTableListDict):
    info = pyqtSignal('PyQt_PyObject')

    def __init__(self, servers,  **kwargs):
        ModelTableListDict.__init__(self, [("#", None, False, None),
                                           ("Title", "title", False, None),
                                           ("Original Title", "original_title", False, None),
                                           ("Genres", "genre_name", False, None),
                                           ("Release date", "release_date", False, None),
                                           ("Vote", "vote_average", False, None),
                                           ("Poster", "poster_path", False, None)], **kwargs)

        PosterManager.__init__(self)

        ServerStateHandler.__init__(self, servers)
        self.genres_model = GenreModel()
        self.refresh()

    def on_connection(self, server_name):
        self.refresh()

    def on_disconnection(self, server_name):
        self.refresh()

    def on_refresh(self, server_name, section):
        if section == "movies":
            self.refresh()

    def get_proxy(self):
        proxy = SortProxy()
        proxy.setSourceModel(self)
        return proxy

    @threaded("httpCom")
    def refresh(self):
        data = []
        self.genres_model.reset()
        for server in self.servers.all():
            for movie in server.get_movies(columns=list(self.get_keys(add=["video_id"]))):
                movie["media_type"] = MEDIA_TYPE_MOVIE
                for genre in movie["genre_name"]:
                    self.genres_model.add(genre)
                data.append(movie)
            for tv in server.get_tv_shows(columns=list(self.get_keys(add=["id"]))):
                tv["media_type"] = MEDIA_TYPE_TV
                for genre in tv["genre_name"]:
                    self.genres_model.add(genre)
                data.append(tv)
        self.reset_data(data)
        self.end_refreshed()

    @threaded("httpCom")
    def get_info(self, video):
        if video["media_type"] == MEDIA_TYPE_MOVIE:
            self.info.emit(list(self.servers.server(video["server"]).get_movies(video_id=video["video_id"]))[0])
        elif video["media_type"] == MEDIA_TYPE_TV:
            tv = list(self.servers.server(video["server"]).get_tv_shows(id=video["id"]))[0]
            tv["media_type"] = MEDIA_TYPE_TV
            self.info.emit(tv)

    def get_decoration_role(self, index):
        if index.column() == 0:
            if self.poster_exists(self.list[index.row()]["poster_path"]):
                return QIcon(QPixmap(self.get_poster_path(self.list[index.row()]["poster_path"], mini=True)))
            else:
                return QIcon(QPixmap("rsc/404.jpg"))
        return QVariant()


class SortProxy(QSortFilterProxyModel):
    def __init__(self, parent=None, *args):
        QSortFilterProxyModel.__init__(self, parent)
        self.sort_key = "title"
        self.reverse = False
        self.filter_genres = []
        self.filter_string = ""
        self.do_sort()

    def set_sort_key(self, key):
        self.sort_key = key
        self.do_sort()

    def set_reverse(self, reverse):
        self.reverse = reverse
        self.do_sort()

    def do_sort(self):
        if self.reverse:
            self.sort(0, order=Qt.DescendingOrder)
        else:
            self.sort(0, order=Qt.AscendingOrder)
        self.invalidate()

    def set_genres(self, genres=None):
        if genres is None or "Tous" in genres:
            self.filter_genres = []
        else:
            self.filter_genres = genres
        self.setFilterWildcard("")

    def set_search_string(self, string):
        self.filter_string = string
        self.setFilterWildcard("")

    def lessThan(self, left_index, right_index):

        left_data = self.sourceModel().data(left_index)
        right_data = self.sourceModel().data(right_index)

        return left_data[self.sort_key] < right_data[self.sort_key]

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        data = self.sourceModel().data(index)
        if data == QVariant():
            return False

        for genre in self.filter_genres:
            if genre not in data["genre_name"]:
                return False

        if not filter_by_string(data, "title", self.filter_string):
            return filter_by_string(data, "original_title", self.filter_string)

        return True