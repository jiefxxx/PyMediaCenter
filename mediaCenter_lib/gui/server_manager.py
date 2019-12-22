from PyQt5.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel, QHBoxLayout, QPushButton, QTabWidget, QListView, \
    QTableView


class ActionBar(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.hbox = QHBoxLayout(self)
        self.button_update_files = QPushButton("Mise à jour fichiers", self)
        self.button_update_files.clicked.connect(self.parent().on_files_update)
        self.button_update_movies = QPushButton("Mise à jour des films", self)
        self.button_update_movies.clicked.connect(self.parent().on_movies_update)
        self.button_update_tvs = QPushButton("Mise à jour des series", self)
        self.button_update_tvs.clicked.connect(self.parent().on_tvs_update)
        self.button_update_genres = QPushButton("Mise à jour des genres", self)
        self.button_update_genres.clicked.connect(self.parent().on_genres_update)
        self.button_reset = QPushButton("Reset database", self)
        self.button_reset.clicked.connect(self.parent().on_reset)
        self.button_reset_movies = QPushButton("Reset database films", self)
        self.button_reset_movies.clicked.connect(self.parent().on_movies_reset)
        self.button_reset_tvs = QPushButton("Reset database series", self)
        self.button_reset_tvs.clicked.connect(self.parent().on_tvs_reset)
        self.hbox.addWidget(self.button_update_files)
        self.hbox.addWidget(self.button_update_movies)
        self.hbox.addWidget(self.button_update_tvs)
        self.hbox.addWidget(self.button_update_genres)
        self.hbox.addWidget(self.button_reset)
        self.hbox.addWidget(self.button_reset_movies)
        self.hbox.addWidget(self.button_reset_tvs)
        self.hbox.addStretch()
        self.setLayout(self.hbox)


class InfoBar(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.hbox = QHBoxLayout(self)
        self.table = QTableView(self)
        self.hbox.addWidget(self.table)
        self.setLayout(self.hbox)

    def reset(self, server):
        self.table.setModel(server.model)


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

    def set_server(self, server_data):
        self.server_name = server_data["server"].name
        self.label_name.setText(server_data["server"].name)
        self.info.reset(server_data["server"])

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

    def on_tvs_update(self):
        if self.server_name:
            self.model.start_script("update_tvs", self.server_name)

    def on_movies_reset(self):
        if self.server_name:
            self.model.start_script("reset_movies", self.server_name)

    def on_tvs_reset(self):
        if self.server_name:
            self.model.start_script("reset_tvs", self.server_name)
