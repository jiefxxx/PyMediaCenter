from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView

from mediaCenter_lib.gui.dialogs import TmdbDialog
from mediaCenter_lib.gui.widget import QIconButton
from mediaCenter_lib.model import UploadVideoModel


class UploadBox(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.hbox = QHBoxLayout()
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.setLayout(self.vbox)

        self.add_button = QIconButton("rsc/icones/add.png", self)
        self.add_button.clicked.connect(self.add)

        self.movie_button = QIconButton("rsc/icones/movies.png", self)
        self.movie_button.clicked.connect(self.info)
        self.del_button = QIconButton("rsc/icones/stop.png", self)
        self.del_button.clicked.connect(self.delete)
        self.send_button = QIconButton("rsc/icones/up.png", self)
        self.send_button.setMinimumHeight(32)
        self.send_button.clicked.connect(self.send)
        self.hbox.addWidget(self.add_button)
        self.hbox.addWidget(self.movie_button)
        self.hbox.addWidget(self.del_button)
        self.hbox.addWidget(self.send_button)
        self.hbox.addStretch(stretch=True)

        self.table = QTableView(self)
        self.model = UploadVideoModel(self.table)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setMaximumSectionSize(700)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.vbox.addWidget(self.table, stretch=True)

    def send(self):
        for index in self.table.selectionModel().selectedRows():
            self.model.send(index)

    def add(self):
        self.model.add()

    def info(self):
        for index in self.table.selectionModel().selectedRows():
            video = self.model.data(index)
            dlg = TmdbDialog(video, self)
            if dlg.exec_() and dlg.info is not None:
                self.model.set_info(index, dlg.info)

    def delete(self):
        for index in self.table.selectionModel().selectedRows():
            self.model.removeRow(index.row())
