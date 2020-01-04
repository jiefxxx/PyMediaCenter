from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QListView, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QComboBox, QCheckBox, QApplication

from mediaCenter_lib.gui.media_info import MediaInfo
from mediaCenter_lib.gui.menu import VideoMenu


class SearchHeader(QWidget):
    def __init__(self, proxy, model_genre, parent):
        QWidget.__init__(self, parent)
        self.proxy = proxy
        self.model_genre = model_genre

        hbox = QHBoxLayout()

        self.search_widget = QLineEdit(self)
        self.search_widget.textEdited.connect(self.proxy.set_search_string)

        self.sort_combo_widget = QComboBox(self)
        self.sort_combo_widget.addItem("Titre", userData="title")
        self.sort_combo_widget.addItem("Titre original", userData="original_title")
        self.sort_combo_widget.addItem("Date de sortie", userData="release_date")
        self.sort_combo_widget.addItem("Vote", userData="vote_average")
        self.sort_combo_widget.currentIndexChanged.connect(self.on_sort_combo)

        self.sort_revers_check = QCheckBox(self)
        self.sort_revers_check.stateChanged.connect(self.on_sort_revers)

        self.genre_combo_widget = QComboBox(self)
        self.model_genre.refreshed.connect(self.on_genre_refreshed)
        self.genre_combo_widget.setModel(self.model_genre)
        self.genre_combo_widget.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.genre_combo_widget.currentIndexChanged.connect(self.on_genre_combo)

        hbox.addWidget(self.sort_combo_widget)
        hbox.addWidget(self.sort_revers_check)
        hbox.addWidget(self.search_widget, stretch=True)
        hbox.addWidget(self.genre_combo_widget)

        self.setLayout(hbox)

    def on_genre_refreshed(self):
        if len(self.proxy.filter_genres) > 0:
            self.genre_combo_widget.setCurrentText(self.proxy.filter_genres[0])
        else:
            self.genre_combo_widget.setCurrentText("Tous")

    def on_sort_combo(self, index):
        self.proxy.set_sort_key(self.sort_combo_widget.itemData(index))

    def on_genre_combo(self, index):
        try:
            self.proxy.set_genres([self.model_genre.data(self.model_genre.index(index, 0))["name"]])
        except TypeError:
            pass

    def on_sort_revers(self, state):
        reverse = False
        if state == Qt.Checked:
            reverse = True

        self.proxy.set_reverse(reverse)


class MediaLibrary(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)

        main_vbox = QVBoxLayout()
        main_hbox = QHBoxLayout()

        self.model = self.window().get_model("media")

        self.proxy = self.model.get_proxy()
        self.proxy.set_sort_key("title")

        self.movie_widget = MediaPosterList(self)
        self.movie_widget.setModel(self.proxy)

        self.selection = self.movie_widget.selectionModel()
        self.selection.selectionChanged.connect(self.on_selection)

        self.movie_info = MediaInfo(self)

        self.header = SearchHeader(self.proxy, self.model.genres_model, self)

        main_vbox.addWidget(self.header)

        main_hbox.addWidget(self.movie_widget, stretch=True)
        main_hbox.addWidget(self.movie_info)

        main_vbox.addLayout(main_hbox)

        self.setLayout(main_vbox)

    def on_menu(self, event):
        proxy_index = self.movie_widget.indexAt(event.pos())
        model_index = self.proxy.mapToSource(proxy_index)
        data = self.model.data(model_index)

        VideoMenu(self.window(), data).popup(QCursor.pos())

    def on_selection(self, item_selection):
        indexes = item_selection.indexes()
        if len(indexes) == 0:
            return
        proxy_index = indexes[0]
        model_index = self.proxy.mapToSource(proxy_index)
        data = self.model.data(model_index)
        self.model.get_info(data)


class MediaPosterList(QListView):
    def __init__(self, parent=None, callback=None):
        QListView.__init__(self, parent)

        rect = QApplication.desktop().screenGeometry()
        self.poster_height = int((rect.width() / 1366) * 230)
        self.poster_width = int((rect.width() / 1366) * 154)

        self.setFlow(QListView.LeftToRight)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)
        self.setUniformItemSizes(True)
        self.setViewMode(QListView.IconMode)
        self.setLayoutMode(QListView.Batched)
        self.setGridSize(QSize(self.poster_width+4, self.poster_height+4))
        self.setIconSize(QSize(self.poster_width, self.poster_height))
        self.setStyleSheet(MoviesListStylesheet)

    def contextMenuEvent(self, event):
        self.parent().on_menu(event)


MoviesListStylesheet = """

QListView {
    show-decoration-selected: 1; /* make the selection span the entire width of the view */
}

QListView::item:alternate {
    background: #EEEEEE;
}

QListView::item:selected {
    border: 2px solid red;
}

QListView::item:selected:!active {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #ABAFE5, stop: 1 #8588B2);
}

QListView::item:selected:active {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #6a6ea9, stop: 1 #888dd9);
}

QListView::item:hover {

}"""

