from PyQt5.QtWidgets import QMenu, QFileDialog

from mediaCenter_lib.gui.dialogs import TmdbDialog, ConfirmationDialog, TmdbTvDialog, TvMakerDialog


class VideoMenu(QMenu):
    def __init__(self, parent, data):
        QMenu.__init__(self, parent)
        self._window = parent

        if type(data) is not list:
            data = [data]
        self.videos = data

        self.addAction("play").triggered.connect(lambda checked: self.parent().test(data))
        self.addAction("delete").triggered.connect(self.video_delete)
        self.addAction("edit movie").triggered.connect(self.video_movie_edit)
        self.addAction("download").triggered.connect(self.video_download)
        self.addAction("edit tv show").triggered.connect(self.video_tv_edit)

    def video_delete(self, checked):
        for video in self.videos:
            conf = ConfirmationDialog("delete video " + str(video["video_id"]), self)
            if conf.exec_():
                self._window.get_model("video").delete(video)

    def video_movie_edit(self, checked):
        for video in self.videos:
            dlg = TmdbDialog("find movie", self)
            if dlg.exec_() and dlg.info is not None:
                dlg_c = ConfirmationDialog("keep data ?")
                if dlg_c.exec_():
                    copy = True
                else:
                    copy = False
                self._window.get_model("video").edit_movie(video, dlg.info["id"], copy=copy)

    def video_tv_edit(self, checked):
        dlg = TmdbTvDialog(self)
        if dlg.exec_() and dlg.info is not None:
            dlg2 = TvMakerDialog(self.videos, dlg.info, self)
            if dlg2.exec_() and dlg2.model.list:
                dlg_c = ConfirmationDialog("keep data ?")
                if dlg_c.exec_():
                    copy = True
                else:
                    copy = False
                for item in dlg2.model.list:
                    self._window.get_model("video").edit_tv(item["video"],
                                                            item["tv_id"],
                                                            item["season_number"],
                                                            item["episode_number"], copy=copy)

    def video_download(self):
        for video in self.videos:
            directory = QFileDialog.getExistingDirectory(None, "Open Directory",
                                                   "/home",
                                                   QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
            if len(directory) > 0:
                self._window.get_model("upload").add_download(video, directory)



