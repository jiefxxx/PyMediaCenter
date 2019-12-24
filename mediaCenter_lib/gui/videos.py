import unicodedata

from PyQt5.QtCore import QSortFilterProxyModel, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView, QLineEdit, \
    QComboBox

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

        self.input = QLineEdit(self)
        self.input.textEdited.connect(self.on_input)
        self.combo_server = QComboBox(self)
        self.combo_server.setModel(self.window().get_model("server"))
        self.combo_server.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combo_server.currentIndexChanged.connect(self.on_combo_server)
        self.hbox.addWidget(self.input, stretch=True)
        self.hbox.addWidget(self.combo_server)

        self.vbox.addLayout(self.hbox)
        self.vbox.addWidget(self.table, stretch=True)

    def on_combo_server(self, index):
        self.proxy.set_server(self.combo_server.currentText())


    def on_input(self, text):
        self.proxy.set_search_string(text)

    def on_menu(self, pos):
        videos = []
        for index in self.table.selectionModel().selectedRows():
            videos.append(self.model.data(index))

        VideoMenu(self.window(), videos).popup(QCursor.pos())


def strip_accents(text):
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)


def filter_by_string(data, key, value):
    if len(value) == 0:
        return True
    data_value = strip_accents(data[key]).lower()
    value = strip_accents(value).lower()
    for val in value.split(" "):
        if data_value.find(val) >= 0 and len(val) > 0:
            return True
    return False


class SortVideo(QSortFilterProxyModel):
    def __init__(self):
        QSortFilterProxyModel.__init__(self, None)
        self.filter_string = ""
        self.server_name = ""

    def set_search_string(self, string):
        self.filter_string = string
        self.setFilterWildcard("")

    def set_server(self, server_name):
        self.server_name = server_name
        self.setFilterWildcard("")

    def lessThan(self, left, right):

        left_data = self.sourceModel().data(left, role=Qt.UserRole)
        right_data = self.sourceModel().data(right, role=Qt.UserRole)

        return left_data > right_data

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        data = self.sourceModel().data(index)

        if not data["server"] == self.server_name:
            return False

        if not filter_by_string(data, "path", self.filter_string):
            return False

        return True

