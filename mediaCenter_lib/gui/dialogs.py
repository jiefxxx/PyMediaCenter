from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QTableView, \
    QHeaderView, QAbstractItemView, QPushButton, QCheckBox

from mediaCenter_lib.gui.widget import WidgetSpinner
from mediaCenter_lib.model.tmdb import TmdbMovieModel, TmdbTvModel
from mediaCenter_lib.model.tv import TvMakerModel


class TmdbDialog(QDialog):

    def __init__(self, path, *args, **kwargs):
        super(TmdbDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle("TMDBFinder")
        self.setMinimumSize(900, 400)

        end_button = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.layout = QVBoxLayout()

        self.label = QLabel(path)

        self.hbox = QHBoxLayout()
        self.input = QLineEdit(self)
        self.spinner = WidgetSpinner(32, 32, self)
        self.hbox.addWidget(self.input)
        self.hbox.addWidget(self.spinner)

        self.table = QTableView(self)
        self.model = TmdbMovieModel()
        self.model.busy.connect(self.on_model_busy)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setMaximumSectionSize(700)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.clicked.connect(self.select_row)

        self.buttonBox = QDialogButtonBox(end_button)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.label)
        self.layout.addLayout(self.hbox)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self.info = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.model.on_search(self.input.text())
            return
        return QDialog.keyPressEvent(self, event)

    def select_row(self, index):
        self.info = self.model.data(index)

    def on_model_busy(self, busy):
        if busy:
            self.spinner.start()
        else:
            self.spinner.stop()


class ConfirmationDialog(QDialog):

    def __init__(self, string, *args, **kwargs):
        QDialog.__init__(self, *args, **kwargs)
        self.setWindowTitle("need confirmation")

        end_button = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.layout = QVBoxLayout()

        self.label = QLabel(string)

        self.buttonBox = QDialogButtonBox(end_button)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class TvMakerDialog(QDialog):
    def __init__(self, videos, tv_show, *args, **kwargs):
        QDialog.__init__(self, *args, **kwargs)
        self.setWindowTitle("Tv Maker")
        self.setMinimumSize(900, 500)

        end_button = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.layout = QVBoxLayout()
        hbox = QHBoxLayout()

        self.model = TvMakerModel(videos, tv_show)
        self.table = QTableView(self)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setMaximumSectionSize(700)
        self.table.setModel(self.model)
        #self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.buttonBox = QDialogButtonBox(end_button)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.input_season = QLineEdit(self)
        self.button_season = QPushButton("set season", self)
        self.button_season.clicked.connect(self.on_season)

        hbox.addWidget(self.input_season)
        hbox.addWidget(self.button_season)
        hbox.addStretch(True)

        self.layout.addLayout(hbox)
        self.layout.addWidget(self.table, stretch=True)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def on_season(self):
        season = int(self.input_season.text())
        self.model.set_season(season)


class TmdbTvDialog(QDialog):

    def __init__(self, path, *args, **kwargs):
        super(TmdbTvDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle("TMDBFinder")
        self.setMinimumSize(900, 400)

        end_button = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.layout = QVBoxLayout()

        self.label = QLabel(path)

        self.hbox = QHBoxLayout()
        self.input = QLineEdit(self)
        self.spinner = WidgetSpinner(32, 32, self)
        self.hbox.addWidget(self.input)
        self.hbox.addWidget(self.spinner)

        self.table = QTableView(self)
        self.model = TmdbTvModel()
        self.model.busy.connect(self.on_model_busy)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setMaximumSectionSize(700)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.clicked.connect(self.select_row)

        self.buttonBox = QDialogButtonBox(end_button)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.label)
        self.layout.addLayout(self.hbox)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self.info = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.model.on_search(self.input.text())
            return
        return QDialog.keyPressEvent(self, event)

    def select_row(self, index):
        self.info = self.model.data(index)

    def on_model_busy(self, busy):
        if busy:
            self.spinner.start()
        else:
            self.spinner.stop()