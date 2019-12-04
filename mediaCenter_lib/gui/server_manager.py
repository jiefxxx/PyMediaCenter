from PyQt5.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel, QHBoxLayout, QPushButton, QTabWidget


class ActionBar(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.hbox = QHBoxLayout(self)
        self.button_update_files = QPushButton("Mise à jour fichiers", self)
        self.button_update_files.clicked.connect(self.parent().on_files_update)
        self.button_update_movies = QPushButton("Mise à jour des films", self)
        self.button_update_movies.clicked.connect(self.parent().on_movies_update)
        self.button_update_genres = QPushButton("Mise à jour des genres", self)
        self.button_update_genres.clicked.connect(self.parent().on_genres_update)
        self.button_reset = QPushButton("Reset database", self)
        self.button_reset.clicked.connect(self.parent().on_reset)
        self.hbox.addWidget(self.button_update_files)
        self.hbox.addWidget(self.button_update_movies)
        self.hbox.addWidget(self.button_update_genres)
        self.hbox.addWidget(self.button_reset)
        self.hbox.addStretch()
        self.setLayout(self.hbox)


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

    def on_progress(self, data):
        self.label_action.setText(data["script"])
        self.label_info.setText(data["string"])
        self.progress.setValue(data["progress"]*2000)


class ServerManager(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.tab = QTabWidget(self)
        self.main_vbox = QVBoxLayout(self)
        self.main_vbox.addWidget(self.tab)
        self.setLayout(self.main_vbox)
        self.server_boxes = []

        for server in self.window().get_model("server").servers.all():
            self.add_server(server.name)

    def add_server(self, server_name):
        server = ServerBox(server_name, self)
        self.tab.addTab(server, server_name)


class ServerBox(QWidget):
    def __init__(self, server_name, parent):
        QWidget.__init__(self, parent)
        self.model = self.window().get_model("server")
        self.server_name = server_name

        self.command = ActionBar(self)
        self.info = InfoBar(self)

        self.main_vbox = QVBoxLayout(self)
        self.main_vbox.addWidget(self.command)
        self.main_vbox.addWidget(self.info)
        self.main_vbox.addStretch()

        self.setLayout(self.main_vbox)

        self.model.get_progress_action(self.server_name).connect(self.info.on_progress)

    def on_reset(self):
        self.model.start_script("reset_database", self.server_name)

    def on_genres_update(self):
        self.model.start_script("update_genres", self.server_name)

    def on_files_update(self):
        self.model.start_script("update_videos", self.server_name)

    def on_movies_update(self):
        self.model.start_script("update_movies", self.server_name)
