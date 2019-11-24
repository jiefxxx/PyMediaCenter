from PyQt5.QtWidgets import QMenu

from mediaCenter_lib.gui.dialogs import TmdbDialog, ConfirmationDialog


class VideoMenu(QMenu):
    def __init__(self, parent, data):
        QMenu.__init__(self, parent)

        self.video_data = data

        self.addAction("play").triggered.connect(lambda checked: self.window().test(data))
        self.addAction("delete").triggered.connect(self.video_delete)
        self.addAction("edit movie").triggered.connect(self.video_movie_edit)
        # self.addAction("edit tv show").triggered.connect(self.video_delete) TODO: TV show codes

    def video_delete(self, checked):
        print(self.video_data)

    def video_movie_edit(self, checked):
        dlg = TmdbDialog("find movie", self)
        if dlg.exec_() and dlg.info is not None:
            conf = ConfirmationDialog("change video to "+dlg.info["title"], self)
            if conf.exec_():
                print("yeah")


