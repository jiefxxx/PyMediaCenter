from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView


class Videos(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.hbox = QHBoxLayout()
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.setLayout(self.vbox)

        self.table = QTableView(self)
        self.model = self.window().get_model("video")
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setMaximumSectionSize(500)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.vbox.addWidget(self.table, stretch=True)