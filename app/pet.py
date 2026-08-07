import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QAction, QApplication, QLabel, QMenu

APP_DIR = Path(__file__).resolve().parent.parent
GIF_PATH = APP_DIR / "app" / "gif" / "idle.gif"


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

        self.movie = QMovie(str(GIF_PATH))
        self.setMovie(self.movie)
        self.movie.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._show_menu(event.globalPos())
        elif event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.drag_position is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = None

    def _show_menu(self, pos):
        menu = QMenu(self)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        menu.exec_(pos)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())