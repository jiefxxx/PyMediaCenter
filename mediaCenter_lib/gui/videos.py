from PyQt5.QtCore import QSortFilterProxyModel, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView

from mediaCenter_lib.gui.menu import VideoMenu


class Videos(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.hbox = QHBoxLayout()
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.setLayout(self.vbox)

        self.table = QTableView(self)
        self.model = self.window().get_model("video")
        self.proxy = SortVideo()
        self.proxy.setSourceModel(self.model)
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setMaximumSectionSize(500)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.on_menu)
        self.table.hideColumn(0)
        self.vbox.addWidget(self.table, stretch=True)

    def on_menu(self, pos):
        proxy_index = self.table.indexAt(pos)
        model_index = self.proxy.mapToSource(proxy_index)
        data = self.model.data(model_index)
        VideoMenu(self.window(), data).popup(QCursor.pos())


class SortVideo(QSortFilterProxyModel):
    def __init__(self):
        QSortFilterProxyModel.__init__(self, None)

    def lessThan(self, left, right):

        left_data = self.sourceModel().data(left, role=Qt.UserRole)
        right_data = self.sourceModel().data(right, role=Qt.UserRole)

        return left_data > right_data

