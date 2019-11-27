import unicodedata

from PyQt5.QtCore import Qt, QSize, QSortFilterProxyModel, QItemSelection, QItemSelectionModel
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtWidgets import QListView, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QComboBox, QCheckBox, QLabel, QMenu

from common_lib.fct import convert_duration, convert_size
from mediaCenter_lib.gui.menu import VideoMenu
from mediaCenter_lib.gui.widget import QIconButton


class Movies(QWidget):
    def __init__(self, parent, callback=None):
        QWidget.__init__(self, parent)

        self.callback = callback

        main_vbox = QVBoxLayout(self)
        main_hbox = QHBoxLayout(self)
        self.top_hbox = QHBoxLayout(self)

        self.model = self.window().get_model("movie")
        self.model.refreshed.connect(self.on_movie_refreshed)

        self.proxy = SortProxy(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.set_sort_key("title")

        self.movie_list = MoviesList(self)
        self.movie_list.setModel(self.proxy)
        self.selModel = self.movie_list.selectionModel()
        self.selModel.selectionChanged.connect(self.on_select)

        self.movie_info = MovieInfo(self)

        self.input = QLineEdit(self)
        self.input.textEdited.connect(self.on_input)

        self.combo_sort = QComboBox(self)
        self.combo_sort.addItem("Titre", userData="title")
        self.combo_sort.addItem("Titre original", userData="original_title")
        self.combo_sort.addItem("Date de sortie", userData="release_date")
        self.combo_sort.addItem("Vote", userData="vote_average")
        self.combo_sort.currentIndexChanged.connect(self.on_sort_combo)

        self.check_reverse = QCheckBox(self)
        self.check_reverse.stateChanged.connect(self.on_sort_reverse)

        self.combo_genre = QComboBox(self)
        self.model_genre = self.window().get_model("genre")
        self.model_genre.refreshed.connect(self.on_genre_refreshed)
        self.combo_genre.setModel(self.model_genre)
        self.combo_genre.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combo_genre.currentIndexChanged.connect(self.on_genre_combo)

        self.refresh_button = QIconButton("rsc/icones/sync.png", self)
        self.refresh_button.clicked.connect(self.on_refresh)

        self.top_hbox.addWidget(self.combo_sort)
        self.top_hbox.addWidget(self.check_reverse)
        self.top_hbox.addWidget(self.input, stretch=True)
        self.top_hbox.addWidget(self.combo_genre)
        self.top_hbox.addWidget(self.refresh_button)

        main_vbox.addLayout(self.top_hbox)

        main_hbox.addWidget(self.movie_list, stretch=True)
        main_hbox.addWidget(self.movie_info)

        main_vbox.addLayout(main_hbox)

        self.setLayout(main_vbox)

    def on_menu(self, event):
        proxy_index = self.movie_list.indexAt(event.pos())
        model_index = self.proxy.mapToSource(proxy_index)
        data = self.model.data(model_index)

        VideoMenu(self.window(), data).popup(QCursor.pos())

    def on_select(self, item_selection):
        indexes = item_selection.indexes()
        if len(indexes) == 0:
            return
        proxy_index = indexes[0]
        model_index = self.proxy.mapToSource(proxy_index)
        data = self.model.data(model_index)
        self.model.get_info(data["video_id"])

    def on_genre_refreshed(self):
        self.combo_genre.setCurrentIndex(self.combo_genre.findText("Tous"))

    def on_movie_refreshed(self):
        self.refresh_button.setStyleSheet("")
        self.movie_list.selectionModel().setCurrentIndex(self.proxy.index(0, 0), QItemSelectionModel.Select)

    def on_refresh(self):
        self.refresh_button.setStyleSheet("QIconButton{background-color: red;}")
        self.model.refresh()

    def on_movie(self, proxy_index):
        model_index = self.proxy.mapToSource(proxy_index)
        if self.callback is not None:
            self.callback(self.model.data(model_index))

    def on_input(self, text):
        self.proxy.set_search_string(text)

    def on_sort_combo(self, index):
        self.proxy.set_sort_key(self.combo_sort.itemData(index))

    def on_genre_combo(self, index):
        try:
            self.proxy.set_genres([self.model_genre.data(self.model_genre.index(index, 0))["name"]])
        except TypeError:
            pass

    def on_sort_reverse(self, state):
        reverse = False
        if state == Qt.Checked:
            reverse = True

        self.proxy.set_reverse(reverse)


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
        for genre in self.filter_genres:
            if genre not in data["genres"]:
                return False

        if not filter_by_string(data, "title", self.filter_string):
            return filter_by_string(data, "original_title", self.filter_string)

        return True


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


class MoviesList(QListView):
    def __init__(self, parent=None, callback=None):
        QListView.__init__(self, parent)

        self.setFlow(QListView.LeftToRight)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)
        self.setUniformItemSizes(True)
        self.setViewMode(QListView.IconMode)
        self.setLayoutMode(QListView.Batched)
        self.setGridSize(QSize(158, 234))
        self.setIconSize(QSize(154, 230))
        self.setStyleSheet(MoviesListStylesheet)

        self.doubleClicked.connect(self.parent().on_movie)

    def contextMenuEvent(self, event):
        self.parent().on_menu(event)


class MovieInfo(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.setFixedWidth(360)

        self.model = parent.model
        self.model.info.connect(self.on_new_movie_info)

        self.poster = QLabel(self)
        pixmap = QPixmap("/home/jief/workspace/python-mediaMananger/rsc/404.jpg")
        self.poster.setPixmap(pixmap)

        self.title = QLabel()
        self.title.setText("Title")
        self.title.setWordWrap(True)

        self.original_title = QLabel()
        self.original_title.setText("Original Title")
        self.original_title.setWordWrap(True)

        self.release = QLabel()
        self.release.setText("Release Date")

        self.vote = QLabel()
        self.vote.setText("0.0")

        self.genres_label = QLabel()
        self.genres_label.setText("No genres")
        self.genres_label.setWordWrap(True)

        self.overview = QLabel()
        self.overview.setText("overview")
        self.overview.setWordWrap(True)

        self.video_id = QLabel()
        self.video_id.setText("video ID: None")

        self.duration = QLabel()
        self.duration.setText("Os")

        self.size = QLabel()
        self.size.setText("0 b")

        self.video_codec = QLabel()
        self.video_codec.setText("Codec: None")

        self.bit_rate = QLabel()
        self.bit_rate.setText(" 0 b/s")

        self.definition = QLabel()
        self.definition.setText("résolution 0px / 0px")

        self.junk = QLabel()
        self.junk.setText("Junk: None")

        self.movie_vbox = QVBoxLayout()
        self.movie_vbox.addWidget(self.title)
        self.movie_vbox.addWidget(self.original_title)
        self.movie_vbox.addWidget(self.release)
        self.movie_vbox.addWidget(self.vote)
        self.movie_vbox.addWidget(self.genres_label)

        movie_hbox = QHBoxLayout()
        movie_hbox.addWidget(self.poster)
        movie_hbox.addLayout(self.movie_vbox, stretch=True)

        duration_hbox = QHBoxLayout()
        duration_hbox.addWidget(self.duration)
        duration_hbox.addWidget(self.size)

        codec_hbox = QHBoxLayout()
        codec_hbox.addWidget(self.video_codec)
        codec_hbox.addWidget(self.bit_rate)

        self.vbox = QVBoxLayout()
        self.vbox.addLayout(movie_hbox)
        self.vbox.addWidget(self.overview)
        self.vbox.addWidget(self.video_id)
        self.vbox.addLayout(duration_hbox)
        self.vbox.addLayout(codec_hbox)
        self.vbox.addWidget(self.definition)
        self.vbox.addWidget(self.junk)
        self.vbox.addStretch()

        self.setLayout(self.vbox)

    def on_new_movie_info(self, movie_info):
        poster_path = self.model.get_poster_path(movie_info["poster_path"], mini=True)
        pixmap = QPixmap(poster_path)
        self.poster.setPixmap(pixmap)

        self.title.setText(movie_info["title"])
        self.original_title.setText(movie_info["original_title"])
        self.release.setText(movie_info["release_date"])
        self.genres_label.setText(str(movie_info["genres"]))
        self.vote.setText(str(movie_info["vote_average"]))

        self.overview.setText(movie_info["overview"])

        self.video_id.setText("video ID: "+str(movie_info["video_id"]))
        self.duration.setText(convert_duration(movie_info["duration"]))
        self.size.setText(convert_size(movie_info["size"]))
        self.video_codec.setText("Codec: "+str(movie_info["codecs_video"]))
        self.bit_rate.setText(convert_size(movie_info["bit_rate"])+"/s")

        self.definition.setText("résolution: "+str(movie_info["width"])+"px / "+str(movie_info["height"])+"px")

        self.junk.setText("Junk : "+str(movie_info["junk"]))
