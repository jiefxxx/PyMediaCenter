from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView, \
    QTabWidget

from common_lib.fct import convert_duration, convert_size
from mediaCenter_lib.gui.menu import VideoMenu


class MovieInfoTable(QTableView):
    def __init__(self, parent):
        self.root = parent
        QTableView.__init__(self, parent)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hideColumn(2)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.root.on_selection_validate()
        elif event.key() == Qt.Key_Escape:
            self.root.on_escape()
        else:
            QTableView.keyPressEvent(self, event)


class MovieInfo(QWidget):
    def __init__(self, parent, medialibray):
        self.medialibrary = medialibray
        QWidget.__init__(self, parent)
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        self.model = self.window().get_model("movie_file")

        self.table = MovieInfoTable(self)
        self.table.customContextMenuRequested.connect(self.on_menu)
        self.table.doubleClicked.connect(self.on_selection_validate)
        self.table.setModel(self.model)

        self.tab = QTabWidget(self)

        self.overview = QLabel()
        self.overview.setText("overview")
        self.overview.setWordWrap(True)

        self.tab.addTab(self.table, "Videos")
        self.tab.addTab(self.overview, "Overview")

        self.vbox.addWidget(self.tab, stretch=True)

    def on_menu(self, pos):
        proxy_index = self.table.indexAt(pos)
        model_index = proxy_index
        data = self.model.data(model_index)
        VideoMenu(self.window(), data).popup(QCursor.pos())

    def set_media(self, media):
        self.model.set_media_id(media["id"])
        self.overview.setText(media["overview"])

    def on_selection_validate(self, ignore=None):
        index = self.table.currentIndex()
        data = self.model.data(index)
        self.window().test([data])

    def on_escape(self):
        self.medialibrary.back_focus()