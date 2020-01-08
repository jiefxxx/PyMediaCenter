import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QStackedWidget, QLabel, QVBoxLayout, QHBoxLayout, QApplication

from common_lib.config import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV
from mediaCenter_lib.gui.media_info.movie_info import MovieInfo
from mediaCenter_lib.gui.media_info.tv_info import TvInfo


class MediaInfo(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.current = MEDIA_TYPE_MOVIE

        rect = QApplication.desktop().screenGeometry()
        self.font_size = int((rect.width() / 1366) * 15)
        self.poster_width = int((rect.width() / 1366) * 154)
        self.pan_width = int((rect.width() / 1366) * 500)
        self.setFixedWidth(self.pan_width)

        self.setStyleSheet("QLabel{font-size: " + str(self.font_size) + "px;}"
                           "QTabWidget{font-size: " + str(self.font_size) + "px;}"
                           "QTableView{font-size: " + str(self.font_size) + "px;}"
                           "QToolTip{font-size: " + str(self.font_size) + "px}")

        self.stack = QStackedWidget(self)

        self.model = parent.model
        self.model.info.connect(self.set_media)

        self.poster = QLabel(self)
        pixmap = QPixmap("./rsc/404.jpg").scaledToWidth(self.poster_width, mode=Qt.SmoothTransformation)
        self.poster.setPixmap(pixmap)

        self.title = QLabel()
        self.title.setText("Title")
        self.title.setWordWrap(True)
        self.title.setStyleSheet("QLabel{font-size: " + str(int(self.font_size * 1.7)) + "px;}")

        self.original_title = QLabel()
        self.original_title.setText("Original Title")
        self.original_title.setWordWrap(True)
        self.original_title.setStyleSheet("QLabel{font-style: italic;}")

        self.release = QLabel()
        self.release.setText("Release Date")

        self.vote = QLabel()
        self.vote.setText("0.0")

        self.genres_label = QLabel()
        self.genres_label.setText("No genres")
        self.genres_label.setWordWrap(True)

        self.movie_info = MovieInfo(self, parent)
        self.tv_info = TvInfo(self, parent)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.movie_info)
        self.stack.addWidget(self.tv_info)

        self.movie_vbox = QVBoxLayout()
        self.movie_vbox.addWidget(self.title)
        self.movie_vbox.addWidget(self.original_title)
        self.movie_vbox.addWidget(self.release)
        self.movie_vbox.addWidget(self.vote)
        self.movie_vbox.addWidget(self.genres_label)
        self.movie_vbox.addStretch(True)

        hbox = QHBoxLayout()
        hbox.addWidget(self.poster)
        hbox.addLayout(self.movie_vbox, stretch=True)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.stack, stretch=True)

        self.setLayout(vbox)

    def focus_table(self, launch=False):
        if self.current == MEDIA_TYPE_MOVIE:
            self.movie_info.table.setFocus()
            self.movie_info.table.setCurrentIndex(self.movie_info.model.index(0, 0))
            if launch:
                self.movie_info.on_selection_validate()
        elif self.current == MEDIA_TYPE_TV:
            self.tv_info.table.setFocus()
            self.tv_info.select_higher()
            if launch:
                self.tv_info.on_selection_validate()

    def set_media(self, media):
        poster_path = self.model.get_poster_path(media["poster_path"], mini=True)
        pixmap = QPixmap(poster_path).scaledToWidth(self.poster_width, mode=Qt.SmoothTransformation)

        self.poster.setPixmap(pixmap)

        self.title.setText(media["title"])
        self.original_title.setText(media["original_title"])
        self.release.setText(media["release_date"])
        self.genres_label.setText(str(media["genre_name"]))
        self.vote.setText(str(media["vote_average"]))

        if media["media_type"] == MEDIA_TYPE_MOVIE:
            self.current = MEDIA_TYPE_MOVIE
            self.movie_info.set_media(media)
            self.stack.setCurrentWidget(self.movie_info)
        elif media["media_type"] == MEDIA_TYPE_TV:
            self.current = MEDIA_TYPE_TV
            self.tv_info.set_media(media)
            self.stack.setCurrentWidget(self.tv_info)

