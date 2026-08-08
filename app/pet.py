import json
import random
import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QAction, QApplication, QLabel, QMenu

APP_DIR = Path(__file__).resolve().parent.parent
GIF_DIR = APP_DIR / "app" / "gif"
SETTINGS_PATH = APP_DIR / "app" / "设置.json"

GIF_ORDER = [
    "idle.gif",
    "expect.gif",
    "pen_idle.gif",
    "draw_continuous.gif",
    "smug.gif",
    "draw_intermittent.gif",
    "think.gif",
]

CLICK_REACTIONS = ["smug.gif", "think.gif", "expect.gif"]


class DesktopPet(QLabel):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.drag_position = None
        self.current_gif = "idle.gif"
        self.is_dragging = False
        self.drag_threshold = 5
        self.press_position = None
        self.pre_action_gif = "idle.gif"
        self.original_size = None
        self.scale_factor = 1.0
        self.saved_pos = None

        settings = self._load_settings()
        if "scale" in settings:
            self.scale_factor = float(settings["scale"])
        if "x" in settings and "y" in settings:
            self.saved_pos = (int(settings["x"]), int(settings["y"]))

        self._initial_position_set = self.saved_pos is not None
        self.setScaledContents(True)

        self.click_recovery = QTimer(self)
        self.click_recovery.setSingleShot(True)
        self.click_recovery.timeout.connect(self._recover_after_click)

        self.movie = QMovie(str(GIF_DIR / self.current_gif))
        self.movie.frameChanged.connect(self._on_frame_changed)
        self.setMovie(self.movie)
        self.movie.start()

        if self.saved_pos is not None:
            self.move(*self.saved_pos)

    def _load_settings(self):
        if SETTINGS_PATH.exists():
            try:
                return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _on_frame_changed(self, _frame_number=0):
        frame = self.movie.currentPixmap()
        if frame.isNull():
            return

        if self.original_size is None:
            self.original_size = (frame.width(), frame.height())
            self._apply_scale()

        if not self._initial_position_set:
            self._initial_position_set = True
            self.move_to_corner()

    def _apply_scale(self):
        if self.original_size is None:
            return
        self.setFixedSize(
            max(1, int(self.original_size[0] * self.scale_factor)),
            max(1, int(self.original_size[1] * self.scale_factor)),
        )

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale_factor *= 1.1
        else:
            self.scale_factor /= 1.1

        self.scale_factor = max(0.5, min(2.0, self.scale_factor))
        self._apply_scale()
        self.save_settings()
        event.accept()

    def move_to_corner(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.width() - self.width() - 100,
            screen.height() - self.height() - 100,
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._show_menu(event.globalPos())
        elif event.button() == Qt.LeftButton:
            self.press_position = event.globalPos()
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.is_dragging = False
            self.pre_action_gif = self.current_gif

    def mouseMoveEvent(self, event):
        if self.drag_position is not None and event.buttons() & Qt.LeftButton:
            distance = (event.globalPos() - self.press_position).manhattanLength()
            if distance > self.drag_threshold:
                self.is_dragging = True
            self.move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_dragging:
                self.is_dragging = False
                self.switch_gif(self.pre_action_gif)
            else:
                self.switch_gif(random.choice(CLICK_REACTIONS))
                self.click_recovery.start(2000)
            self.drag_position = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            current_index = GIF_ORDER.index(self.current_gif)
            next_index = (current_index + 1) % len(GIF_ORDER)
            self.switch_gif(GIF_ORDER[next_index])

    def switch_gif(self, name):
        if name == self.current_gif:
            return
        path = GIF_DIR / name
        if not path.exists():
            return

        self.current_gif = name
        self.movie.stop()
        self.original_size = None
        self.movie = QMovie(str(path))
        self.movie.frameChanged.connect(self._on_frame_changed)
        self.setMovie(self.movie)
        self.movie.start()

    def _recover_after_click(self):
        self.switch_gif("idle.gif")

    def reset_position_and_size(self):
        self.scale_factor = 1.0
        self._apply_scale()
        self.move_to_corner()
        self.save_settings()

    def save_settings(self):
        data = {
            "x": self.pos().x(),
            "y": self.pos().y(),
            "scale": self.scale_factor,
        }
        try:
            SETTINGS_PATH.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def do_quit(self):
        self.save_settings()
        QApplication.quit()

    def _show_menu(self, pos):
        menu = QMenu(self)

        reset_action = QAction("重置位置和大小", self)
        reset_action.triggered.connect(self.reset_position_and_size)
        menu.addAction(reset_action)

        menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.do_quit)
        menu.addAction(quit_action)

        menu.exec_(pos)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())