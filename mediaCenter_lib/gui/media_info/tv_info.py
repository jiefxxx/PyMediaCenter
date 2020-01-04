from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView, QTabWidget, QLabel

from mediaCenter_lib.gui.menu import VideoMenu
from mediaCenter_lib.model.tv import SortEpisode


class TvInfo(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        self.model = self.window().get_model("tv_episode")

        self.proxy = self.model.get_proxy()

        self.table = QTableView(self)

        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.on_menu)
        self.table.hideColumn(1)
        self.table.hideColumn(5)

        self.tab = QTabWidget(self)

        self.overview = QLabel()
        self.overview.setText("overview")
        self.overview.setWordWrap(True)

        self.tab.addTab(self.table, "Episodes")
        self.tab.addTab(self.overview, "Overview")

        self.vbox.addWidget(self.tab, stretch=True)

    def on_menu(self, pos):
        proxy_index = self.table.indexAt(pos)
        model_index = self.proxy.mapToSource(proxy_index)
        data = self.model.data(model_index)
        VideoMenu(self.window(), data).popup(QCursor.pos())

    def set_media(self, media):
        self.model.set_tv_id(media["id"])
        self.overview.setText(media["overview"])
        self.proxy.do_sort()
