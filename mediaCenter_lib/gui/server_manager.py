from PyQt5.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel, QHBoxLayout, QPushButton, QTabWidget, QListView


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

    def reset(self):
        self.label_action.setText("None")
        self.label_info.setText("None")
        self.progress.setValue(0)

    def on_progress(self, data):
        self.label_action.setText(data["script"])
        self.label_info.setText(data["string"])
        self.progress.setValue(data["progress"]*2000)


class ServerManager(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.model = self.window().get_model("server")
        self.server_list = QListView(self)
        self.server_list.setModel(self.model)

        self.server_info = ServerBox(None, self)

        self.main_hbox = QHBoxLayout(self)
        self.main_hbox.addWidget(self.server_list)
        self.main_hbox.addWidget(self.server_info, stretch=True)
        self.setLayout(self.main_hbox)

        self.selModel = self.server_list.selectionModel()
        self.selModel.selectionChanged.connect(self.on_select)

    def on_select(self, item_selection):
        indexes = item_selection.indexes()
        if len(indexes) == 0:
            return
        model_index = indexes[0]
        data = self.model.data(model_index)
        self.server_info.set_server(data)


class ServerBox(QWidget):
    def __init__(self, server_name, parent):
        QWidget.__init__(self, parent)
        self.model = self.window().get_model("server")
        self.server_name = server_name

        self.command = ActionBar(self)
        self.info = InfoBar(self)

        self.label_name = QLabel("none", self)

        self.main_vbox = QVBoxLayout(self)
        self.main_vbox.addWidget(self.label_name)
        self.main_vbox.addWidget(self.command)
        self.main_vbox.addWidget(self.info)
        self.main_vbox.addStretch()

        self.setLayout(self.main_vbox)
        self.reset_progress_handler(None)

    def reset_progress_handler(self, server_name):
        if self.server_name:
            self.model.get_progress_action(self.server_name).disconnect(self.info.on_progress)
        self.info.reset()
        if server_name:
            self.server_name = server_name
            self.label_name.setText(self.server_name)
            if self.model.get_last_progress(self.server_name):
                self.info.on_progress(self.model.get_last_progress(self.server_name))
            self.model.get_progress_action(self.server_name).connect(self.info.on_progress)

    def set_server(self, server_data):
        self.reset_progress_handler(server_data["name"])

    def on_reset(self):
        if self.server_name:
            self.model.start_script("reset_database", self.server_name)

    def on_genres_update(self):
        if self.server_name:
            self.model.start_script("update_genres", self.server_name)

    def on_files_update(self):
        if self.server_name:
            self.model.start_script("update_videos", self.server_name)

    def on_movies_update(self):
        if self.server_name:
            self.model.start_script("update_movies", self.server_name)
