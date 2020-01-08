from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView, QTabWidget, QLabel

from mediaCenter_lib.gui.menu import VideoMenu
from mediaCenter_lib.model.tv import SortEpisode


class TvInfoTable(QTableView):
    def __init__(self, parent):
        self.root = parent
        QTableView.__init__(self, parent)
        self.setSortingEnabled(False)
        self.verticalHeader().setVisible(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.root.on_selection_validate()
        elif event.key() == Qt.Key_Escape:
            self.root.on_escape()
        else:
            QTableView.keyPressEvent(self, event)


class TvInfo(QWidget):
    def __init__(self, parent, medialibray):
        self.medialibrary = medialibray
        QWidget.__init__(self, parent)
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        self.model = self.window().get_model("tv_episode")

        self.proxy = self.model.get_proxy()

        self.table = TvInfoTable(self)
        self.table.setModel(self.proxy)
        self.table.customContextMenuRequested.connect(self.on_menu)
        self.table.doubleClicked.connect(self.on_selection_validate)
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

    def on_selection_validate(self, ignore=None):
        ret = []
        row = self.table.currentIndex().row()
        while True:
            proxy_index = self.proxy.index(row, 0)
            index = self.proxy.mapToSource(proxy_index)
            data = self.model.data(index)
            if type(data) is not QVariant:
                ret.append(data)
            else:
                break
            row += 1
        self.window().test(ret)

    def select_higher(self):
        row = 0
        final_index = self.proxy.index(row, 0)

        while True:
            proxy_index = self.proxy.index(row, 0)
            index = self.proxy.mapToSource(proxy_index)
            data = self.model.data(index)
            if type(data) is QVariant:
                break
            if data["last_time"] is not None:
                final_index = proxy_index
            row += 1
            print(data)

        self.table.setCurrentIndex(final_index)

    def on_escape(self):
        self.medialibrary.back_focus()
