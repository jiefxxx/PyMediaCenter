from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtWidgets import QSlider, QLabel, QStyle


class WidgetSpinner(QLabel):
    def __init__(self, w, h, parent):
        QLabel.__init__(self, parent)
        self.movie = QMovie("/home/jief/workspace/python-mediaMananger/rsc/loading.gif")
        self.movie.setScaledSize(QSize(w, h))
        self.setMovie(self.movie)
        self.setVisible(False)

    def start(self):
        self.movie.start()
        self.setVisible(True)

    def stop(self):
        self.setVisible(False)
        self.movie.stop()


class QIconButton(QLabel):
    clicked = pyqtSignal()

    def __init__(self, path, parent=None):
        QLabel.__init__(self, parent)
        self._pixmap = QPixmap(path)
        # self.setPixmap(self._pixmap)

    def resizeEvent(self, event):
        h = self.height()
        tmp_pixmap = self._pixmap.scaled(1000, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(tmp_pixmap)

    def mousePressEvent(self, ev):
        self.clicked.emit()


class QJumpSlider(QSlider):

    def mousePressEvent(self, ev):
        """ Jump to click position """
        self.setValue(QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), ev.x(), self.width()))

    def mouseMoveEvent(self, ev):
        """ Jump to pointer position while moving """
        self.setValue(QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), ev.x(), self.width()))
