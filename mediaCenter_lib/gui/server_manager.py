from PyQt5.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel, QHBoxLayout, QPushButton

class ActionBar(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.hbox = QHBoxLayout(self)
        self.button_update_files = QPushButton("Mise à jour fichiers", self)
        self.button_update_files.clicked.connect(self.on_files_update)
        self.button_update_movies = QPushButton("Mise à jour des films", self)
        self.button_update_movies.clicked.connect(self.on_movies_update)
        self.button_update_genres = QPushButton("Mise à jour des genres", self)
        self.button_update_genres.clicked.connect(self.on_genres_update)
        self.hbox.addWidget(self.button_update_files)
        self.hbox.addWidget(self.button_update_movies)
        self.hbox.addWidget(self.button_update_genres)
        self.hbox.addStretch()
        self.setLayout(self.hbox)

    def on_genres_update(self):
        self.parent().model.start_script("update_genres")

    def on_files_update(self):
        self.parent().model.start_script("update_videos")

    def on_movies_update(self):
        self.parent().model.start_script("update_movies")


class InfoBar(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.hbox = QHBoxLayout(self)

        label_pre_action = QLabel("action en cours", self)
        self.label_action = QLabel("None", self)
        label_pre_info = QLabel("Info : ", self)
        self.label_info = QLabel("None", self)
        self.progress = QProgressBar(self)
        self.progress.setMinimum(0)
        self.progress.setMaximum(2000)

        self.hbox.addWidget(label_pre_action)
        self.hbox.addWidget(self.label_action)
        self.hbox.addWidget(label_pre_info)
        self.hbox.addWidget(self.label_info)
        self.hbox.addWidget(self.progress)
        self.hbox.addStretch()

        self.setLayout(self.hbox)

        self.parent().model.progress.connect(self.on_progress)

    def on_progress(self, data):
        self.label_action.setText(data["script"])
        self.label_info.setText(data["string"])
        self.progress.setValue(data["progress"]*2000)


class ServerManager(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.model = self.window().get_model("serveAction")
        self.command = ActionBar(self)
        self.info = InfoBar(self)

        self.main_vbox = QVBoxLayout(self)
        self.main_vbox.addWidget(self.command)
        self.main_vbox.addWidget(self.info)
        self.main_vbox.addStretch()

        self.setLayout(self.main_vbox)
