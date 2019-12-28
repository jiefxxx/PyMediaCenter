import unicodedata

from PyQt5.QtCore import QSortFilterProxyModel, Qt, QVariant
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView, QLineEdit, \
    QComboBox, QCheckBox

from common_lib.config import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_UNKNOWN, MEDIA_TYPE_ALL
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

        self.model_server = self.window().get_model("server")
        self.model_server.servers.connected.connect(self.on_server_connection)

        all_servers = list(self.model_server.servers.all())
        if len(all_servers) > 0:
            self.proxy.set_server(all_servers[0].name)


        self.combo_server = QComboBox(self)
        self.combo_server.setModel(self.model_server)
        self.combo_server.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combo_server.currentIndexChanged.connect(self.on_combo_server)

        self.check_media_id = QCheckBox(self)
        self.check_media_id.stateChanged.connect(self.on_check_media_id)

        self.combo_type = QComboBox(self)
        self.combo_type.addItem("movies", userData=MEDIA_TYPE_MOVIE)
        self.combo_type.addItem("tvs", userData=MEDIA_TYPE_TV)
        self.combo_type.addItem("unknowns", userData=MEDIA_TYPE_UNKNOWN)
        self.combo_type.currentIndexChanged.connect(self.on_combo_type)
        self.combo_type.setCurrentText("unknowns")

        self.hbox.addWidget(self.combo_type)
        self.hbox.addWidget(self.check_media_id)
        self.hbox.addWidget(self.input, stretch=True)
        self.hbox.addWidget(self.combo_server)

        self.vbox.addLayout(self.hbox)
        self.vbox.addWidget(self.table, stretch=True)

    def on_check_media_id(self, state):
        reverse = False
        if state == Qt.Checked:
            reverse = True

        self.proxy.set_unknown_media(reverse)

    def on_server_connection(self, server_name):
        if self.proxy.server_name == "":
            self.proxy.set_server(server_name)

    def on_combo_type(self, index):
        self.proxy.set_type(self.combo_type.itemData(index, role=Qt.UserRole))

    def on_combo_server(self, index):
        self.proxy.set_server(self.combo_server.currentText())

    def on_input(self, text):
        self.proxy.set_search_string(text)

    def on_menu(self, pos):
        videos = []
        for index in self.table.selectionModel().selectedRows():
            model_index = self.proxy.mapToSource(index)
            videos.append(self.model.data(model_index))

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
        self.only_unknown = False
        self.type = MEDIA_TYPE_UNKNOWN

    def set_unknown_media(self, b):
        self.only_unknown = b
        self.setFilterWildcard("")

    def set_search_string(self, string):
        self.filter_string = string
        self.setFilterWildcard("")

    def set_server(self, server_name):
        self.server_name = server_name
        self.setFilterWildcard("")

    def set_type(self, t):
        self.type = t
        self.setFilterWildcard("")

    def lessThan(self, left, right):

        left_data = self.sourceModel().data(left, role=Qt.UserRole)
        right_data = self.sourceModel().data(right, role=Qt.UserRole)

        return left_data > right_data

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        data = self.sourceModel().data(index)
        if data == QVariant():
            return False

        if not data["server"] == self.server_name:
            return False

        if not data["media_type"] == self.type:
            return False

        if self.only_unknown and data["media_id"] is not None:
            return False

        if not filter_by_string(data, "path", self.filter_string):
            return False

        return True

