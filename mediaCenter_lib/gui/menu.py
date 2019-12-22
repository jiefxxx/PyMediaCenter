from PyQt5.QtWidgets import QMenu, QFileDialog

from mediaCenter_lib.gui.dialogs import TmdbDialog, ConfirmationDialog


class VideoMenu(QMenu):
    def __init__(self, parent, data):
        QMenu.__init__(self, parent)
        self._window = parent

        self.video = data

        self.addAction("play").triggered.connect(lambda checked: self.parent().test(data))
        self.addAction("delete").triggered.connect(self.video_delete)
        self.addAction("edit movie").triggered.connect(self.video_movie_edit)
        self.addAction("download").triggered.connect(self.video_download)
        # self.addAction("edit tv show").triggered.connect(self.video_delete) TODO: TV show codes

    def video_delete(self, checked):
        conf = ConfirmationDialog("delete video " + str(self.video["video_id"]), self)
        if conf.exec_():
            self._window.get_model("video").delete(self.video)

    def video_movie_edit(self, checked):
        dlg = TmdbDialog("find movie", self)
        if dlg.exec_() and dlg.info is not None:
            self._window.get_model("video").edit(self.video, 1, dlg.info["id"])

    def video_download(self):
        directory = QFileDialog.getExistingDirectory(None, "Open Directory",
                                               "/home",
                                               QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if len(directory) > 0:
            self._window.get_model("upload").add_download(self.video, directory)



