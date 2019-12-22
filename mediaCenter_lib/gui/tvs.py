from PyQt5.QtCore import QSortFilterProxyModel, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTableView, QAbstractItemView, QHeaderView

from mediaCenter_lib.gui.menu import VideoMenu
from mediaCenter_lib.gui.movies import MoviesList


class Tvs(QWidget):
    def __init__(self, parent, callback=None):
        QWidget.__init__(self, parent)

        self.callback = callback

        self.top_hbox = QHBoxLayout()
        main_vbox = QVBoxLayout()
        main_hbox = QHBoxLayout()

        self.model = self.window().get_model("tv_show")

        self.tv_list = MoviesList(self)
        self.tv_list.setModel(self.model)
        self.selModel = self.tv_list.selectionModel()
        self.selModel.selectionChanged.connect(self.on_select)

        self.episode_info = TvInfo(self)

        main_vbox.addLayout(self.top_hbox)

        main_hbox.addWidget(self.tv_list, stretch=True)
        main_hbox.addWidget(self.episode_info)

        main_vbox.addLayout(main_hbox)

        self.setLayout(main_vbox)

    def on_movie(self, proxy_index):
        data = self.model.data(proxy_index)
        self.episode_info.proxy.tv_id = data["id"]
        self.episode_info.proxy.do_sort()

    def on_select(self, item_selection):
        indexes = item_selection.indexes()
        if len(indexes) == 0:
            return
        proxy_index = indexes[0]
        data = self.model.data(proxy_index)
        self.episode_info.proxy.tv_id = data["id"]
        self.episode_info.proxy.do_sort()

    def on_menu(self, event):
        pass


class TvInfo(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.setFixedWidth(360)

        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        self.model = self.window().get_model("tv_episode")

        self.proxy = SortEpisode()
        self.proxy.setSourceModel(self.model)

        self.table = QTableView(self)

        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.on_menu)
        self.table.hideColumn(0)
        self.table.hideColumn(1)
        self.table.hideColumn(5)
        self.vbox.addWidget(self.table, stretch=True)

    def on_menu(self, pos):
        proxy_index = self.table.indexAt(pos)
        model_index = self.proxy.mapToSource(proxy_index)
        data = self.model.data(model_index)
        VideoMenu(self.window(), data).popup(QCursor.pos())


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

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        data = self.sourceModel().data(index)
        if data["tv_id"] != self.tv_id:
            return False

        return True

    def do_sort(self):
        if self.reverse:
            self.sort(0, order=Qt.DescendingOrder)
        else:
            self.sort(0, order=Qt.AscendingOrder)
        self.invalidate()

