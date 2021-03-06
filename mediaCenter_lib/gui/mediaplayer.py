import sys
import time

from common_lib.config import MEDIA_TYPE_TV
from common_lib.fct import convert_duration
from mediaCenter_lib.gui.dialogs import ConfirmationDialog
from mediaCenter_lib.gui.widget import QIconButton, QJumpSlider

from PyQt5.QtCore import Qt, QTimer, QSize, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QPainter
from PyQt5.QtWidgets import QWidget, QFrame, QHBoxLayout, QLayout, QMenu, QStyle, QStyleOption, QLabel

import vlc


class MediaPlayer(QWidget):
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.videos = []
        self.current_video = None
        self.last_move = time.time()
        self.setMouseTracking(True)
        self.video_model = self.window().get_model("video")

        self.layout = PlayerLayout(self)
        self.setLayout(self.layout)

        self.screen = Screen(self)
        self.controllers = Controllers(self)

        self.layout.set_screen(self.screen)
        self.layout.set_controllers(self.controllers)

        # creating a basic vlc instance
        self.instance = vlc.Instance()
        # creating an empty vlc media player
        self.media_player = self.instance.media_player_new()
        self.media_player.video_set_mouse_input(0)
        self.media_player.video_set_key_input(0)

        if sys.platform.startswith('linux'):  # for Linux using the X Server
            self.media_player.set_xwindow(self.screen.winId())
        elif sys.platform == "win32":  # for Windows
            self.media_player.set_hwnd(self.screen.winId())

        events = self.media_player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self.media_finished)
        self.finished.connect(self.on_finished)

        self.is_playing = False

        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(200)
        self.ui_timer.timeout.connect(self.update_ui)

        self.pos_timer = QTimer(self)
        self.pos_timer.setInterval(60*1000)
        self.pos_timer.timeout.connect(self.update_last_time)

        self.ui_timer.start()
        self.pos_timer.start()

        self.prevent_next_signal = False

        self.old_window_state = None

    def on_finished(self):
        if len(self.videos) > 0:
            self.play_next()
        else:
            self.stop()

    def media_finished(self, event):
        self.finished.emit()

    def set_videos(self, videos):
        self.videos = videos
        self.play_next()

    def play_next(self):
        video = self.videos.pop(0)
        print(video)
        self.play_video(video)

    def play_video(self, video):
        video = self.video_model.get_video(video)
        if video is None:
            return False
        self.load(self.video_model.get_uri(video))
        self.current_video = video
        last_time = video.get("last_time", None)
        if last_time:
            conf = ConfirmationDialog("Reprendre la lecture à :\r\n " + convert_duration(last_time), self)
            if conf.exec_():
                self.media_player.set_time(last_time)
                return True
        self.current_video["last_time"] = 0
        return True

    def update_last_time(self):
        if not self.current_video:
            return
        current = int(self.media_player.get_time())
        self.current_video["last_time"] = current
        self.video_model.update_last_time(self.current_video)

    def update_ui(self):
        total = int(self.media_player.get_length())
        current = int(self.media_player.get_time())
        self.controllers.set_position(self.media_player.get_position())
        self.controllers.set_timing(current, total)
        if self.last_move+3 < time.time() and self.controllers.isVisible():
            self.controllers.setVisible(False)
            if not self.controllers.isVisible():
                self.setCursor(Qt.BlankCursor)

    def load(self, filename):
        media = self.instance.media_new(filename)
        self.media_player.set_media(media)

        media.parse()
        self.setWindowTitle(media.get_meta(0))

        self.play()

    def play(self):
        if self.media_player.is_playing():
            self.update_last_time()
            self.media_player.pause()
            self.update_last_time()
            self.is_playing = False
        else:
            self.media_player.play()
            self.is_playing = True

    def stop(self):
        self.update_last_time()
        self.media_player.stop()
        self.is_playing = False
        self.window().full_screen(False)
        self.window().on_close_player()

    def toggle_full_screen(self):
        self.window().full_screen()

    def move_position(self, position):
        self.media_player.set_position(position / 1000.0)

    def set_position(self):
        if not self.prevent_next_signal:
            self.media_player.set_position(self.controllers.slider.value()/1000.0)
            self.update_last_time()
        else:
            print("prevented")
            self.prevent_next_signal = False

    def set_audio_track(self, track):
        self.media_player.audio_set_track(track)

    def set_subtitles_track(self, track):
        self.media_player.video_set_spu(track)

    def set_audio_device(self, device):
        self.media_player.pause()
        self.media_player.audio_output_device_set(None, device)
        time.sleep(0.05)
        self.media_player.pause()

    def menu_audio_subtitles(self):
        devices = []
        mods = self.media_player.audio_output_device_enum()

        if mods:
            mod = mods
            while mod:
                mod = mod.contents
                devices.append(mod.device)
                mod = mod.next

        vlc.libvlc_audio_output_device_list_release(mods)
        audio = self.media_player.audio_get_track_description()
        subtitles = self.media_player.video_get_spu_description()

        menu = QMenu(self.controllers.button_str)

        menu.addSection("Audio Output")
        for el in devices:
            action = menu.addAction(el.decode().split('.')[-1])
            action.triggered.connect(lambda checked, device=el: self.set_audio_device(device))

        menu.addSection("Pistes Audio")
        for el in audio:
            action = menu.addAction(el[1].decode())
            action.triggered.connect(lambda checked, track=el[0]: self.set_audio_track(track))

        menu.addSection("Sous-titres")
        for el in subtitles:
            action = menu.addAction(el[1].decode())
            action.triggered.connect(lambda checked, track=el[0]: self.set_subtitles_track(track))

        x = self.controllers.button_str.x()
        y = self.controllers.button_str.y()

        menu.popup(self.controllers.mapToGlobal(QPoint(x, y)))

    def mouseMoveEvent(self, mouse_event):
        self.last_move = time.time()
        if not self.controllers.isVisible():
            self.controllers.setVisible(True)
        self.unsetCursor()
        QWidget.mouseMoveEvent(self, mouse_event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.play()
        elif event.key() == Qt.Key_Escape:
            self.stop()
        elif event.key() == Qt.Key_N:
            self.play_next()
        elif event.key() == Qt.Key_Left:
            self.media_player.set_time(self.media_player.get_time() - 15 * 1000)
        elif event.key() == Qt.Key_Right:
            self.media_player.set_time(self.media_player.get_time() + 15 * 1000)
        elif event.key() == Qt.Key_Down:
            self.media_player.set_time(self.media_player.get_time() - 3 * 60 * 1000)
        elif event.key() == Qt.Key_Up:
            self.media_player.set_time(self.media_player.get_time() + 3 * 60 * 1000)


class Screen(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setMouseTracking(True)


class Controllers(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setMouseTracking(True)
        self.hbox = QHBoxLayout()
        self.setLayout(self.hbox)
        self.visible = True

        self.button_play = QIconButton("rsc/icones/play.png", self)
        self.button_play.clicked.connect(parent.play)
        self.hbox.addWidget(self.button_play)

        self.button_stop = QIconButton("rsc/icones/stop.png", self)
        self.button_stop.clicked.connect(parent.stop)
        self.hbox.addWidget(self.button_stop)

        self.label_position_time = QLabel("--:--:--", self)
        self.hbox.addWidget(self.label_position_time)

        self.slider = QJumpSlider(Qt.Horizontal, self)
        self.slider.setMaximum(1000)
        self.slider.sliderMoved.connect(parent.move_position)
        self.slider.valueChanged.connect(parent.set_position)
        self.slider.setFocusPolicy(Qt.NoFocus)
        self.hbox.addWidget(self.slider)

        self.label_remaining_time = QLabel("--:--:--", self)
        self.hbox.addWidget(self.label_remaining_time)

        self.button_str = QIconButton("rsc/icones/languages.png", self)
        self.button_str.clicked.connect(parent.menu_audio_subtitles)
        self.hbox.addWidget(self.button_str)

        self.button_fs = QIconButton("rsc/icones/full_screen.png", self)
        self.button_fs.clicked.connect(parent.toggle_full_screen)
        self.hbox.addWidget(self.button_fs)

        self.setStyleSheet("Controllers{background-color: rgba(255, 255, 255, 50);}")

        self._parent = parent

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)
        QWidget.paintEvent(self, event)

    def set_position(self, position):
        self.slider.valueChanged.disconnect(self.parent().set_position)
        self.slider.setValue(position*1000)
        self.slider.valueChanged.connect(self.parent().set_position)

    def set_timing(self, timing, total_time):
        self.label_position_time.setText(convert_duration(timing))
        self.label_remaining_time.setText(convert_duration(total_time-timing))


class PlayerLayout(QLayout):
    def __init__(self, parent=None):
        QLayout.__init__(self, parent)
        self.list = []
        self.screen = None
        self.controllers = None

    def set_screen(self, screen):
        self.screen = screen
        self.addWidget(self.screen)

    def set_controllers(self, controllers):
        self.controllers = controllers
        self.addWidget(self.controllers)

    def count(self):
        return len(self.list)

    def itemAt(self, i):
        if 0 <= i < len(self.list):
            return self.list[i]

    def sizeHint(self):
        return QSize(640, 480)

    def addItem(self, item):
        self.list.append(item)

    def setGeometry(self, top_rec):
        QLayout.setGeometry(self, top_rec)
        if self.screen:
            self.screen.setGeometry(0, 0, top_rec.width(), top_rec.height())
        controllers_height = top_rec.height()/100*7
        if controllers_height < 40:
            controllers_height = 40
        if self.controllers:
            self.controllers.setGeometry(QRect(0, top_rec.height()-controllers_height,
                                               top_rec.width(), controllers_height))
