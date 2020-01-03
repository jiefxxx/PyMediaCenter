from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QStackedWidget, QLabel, QVBoxLayout, QHBoxLayout

from common_lib.config import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV
from mediaCenter_lib.gui.media_info.movie_info import MovieInfo
from mediaCenter_lib.gui.media_info.tv_info import TvInfo


class MediaInfo(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.setFixedWidth(500)

        self.stack = QStackedWidget(self)

        self.model = parent.model
        self.model.info.connect(self.set_media)

        self.poster = QLabel(self)
        pixmap = QPixmap("./rsc/404.jpg")
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

        self.movie_info = MovieInfo(self)
        self.tv_info = TvInfo(self)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.movie_info)
        self.stack.addWidget(self.tv_info)

        self.movie_vbox = QVBoxLayout()
        self.movie_vbox.addWidget(self.title)
        self.movie_vbox.addWidget(self.original_title)
        self.movie_vbox.addWidget(self.release)
        self.movie_vbox.addWidget(self.vote)
        self.movie_vbox.addWidget(self.genres_label)

        hbox = QHBoxLayout()
        hbox.addWidget(self.poster)
        hbox.addLayout(self.movie_vbox, stretch=True)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.stack, stretch=True)

        self.setLayout(vbox)

    def set_media(self, media):
        poster_path = self.model.get_poster_path(media["poster_path"], mini=True)
        pixmap = QPixmap(poster_path)
        self.poster.setPixmap(pixmap)

        self.title.setText(media["title"])
        self.original_title.setText(media["original_title"])
        self.release.setText(media["release_date"])
        self.genres_label.setText(str(media["genre_name"]))
        self.vote.setText(str(media["vote_average"]))

        if media["media_type"] == MEDIA_TYPE_MOVIE:
            self.movie_info.set_media(media)
            self.stack.setCurrentWidget(self.movie_info)
        elif media["media_type"] == MEDIA_TYPE_TV:
            self.tv_info.set_media(media)
            self.stack.setCurrentWidget(self.tv_info)