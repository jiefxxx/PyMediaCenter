import unicodedata

from PyQt5.QtCore import Qt, QSize, QSortFilterProxyModel
from PyQt5.QtWidgets import QListView, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QComboBox, QCheckBox

from mediaCenter_lib.gui.widget import QIconButton
from mediaCenter_lib.model import MovieModel, GenreModel


class Movies(QWidget):
    def __init__(self, parent, callback=None):
        QWidget.__init__(self, parent)

        self.callback = callback

        main_vbox = QVBoxLayout(self)
        self.top_hbox = QHBoxLayout(self)

        self.model = self.window().get_model("movie")
        self.model.refreshed.connect(self.on_movie_refreshed)

        self.proxy = SortProxy(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.set_sort_key("title")

        self.movie_list = MoviesList(self)
        self.movie_list.setModel(self.proxy)

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
        main_vbox.addWidget(self.movie_list)

        self.setLayout(main_vbox)

    def on_genre_refreshed(self):
        self.combo_genre.setCurrentIndex(self.combo_genre.findText("Tous"))

    def on_movie_refreshed(self):
        self.refresh_button.setStyleSheet("")

    def on_refresh(self):
        self.refresh_button.setStyleSheet("QIconButton{background-color: rgba(255, 255, 255, 50);}")
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


class MoviesList(QListView):
    def __init__(self, parent=None, callback=None):
        QListView.__init__(self, parent)

        self.setFlow(QListView.LeftToRight)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)
        self.setUniformItemSizes(True)
        self.setViewMode(QListView.IconMode)
        self.setLayoutMode(QListView.Batched)
        self.setGridSize(QSize(154, 250))
        self.setIconSize(QSize(154, 231))

        self.doubleClicked.connect(self.parent().on_movie)
