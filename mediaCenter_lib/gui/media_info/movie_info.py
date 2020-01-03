from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout

from common_lib.fct import convert_duration, convert_size


class MovieInfo(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)

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

        duration_hbox = QHBoxLayout()
        duration_hbox.addWidget(self.duration)
        duration_hbox.addWidget(self.size)

        codec_hbox = QHBoxLayout()
        codec_hbox.addWidget(self.video_codec)
        codec_hbox.addWidget(self.bit_rate)

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.overview)
        self.vbox.addWidget(self.video_id)
        self.vbox.addLayout(duration_hbox)
        self.vbox.addLayout(codec_hbox)
        self.vbox.addWidget(self.definition)
        self.vbox.addWidget(self.junk)
        self.vbox.addStretch()

        self.setLayout(self.vbox)

    def set_media(self, movie_info):
        self.overview.setText(movie_info["overview"])

        self.video_id.setText("video ID: "+str(movie_info["server"])+":"+str(movie_info["video_id"]))
        self.duration.setText(convert_duration(movie_info["duration"]))
        self.size.setText(convert_size(movie_info["size"]))
        self.video_codec.setText("Codec: "+str(movie_info["codecs_video"]))
        self.bit_rate.setText(convert_size(movie_info["bit_rate"])+"/s")

        self.definition.setText("résolution: "+str(movie_info["width"])+"px / "+str(movie_info["height"])+"px")

        self.junk.setText("Junk : "+str(movie_info["junk"]))