import sys
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor

class RegionSelector(QWidget):
    closed = pyqtSignal()  

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowOpacity(0.3)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.showMaximized()
        self.startPoint = None
        self.endPoint = None
        self.isSelecting = False

    def mousePressEvent(self, event):
        self.startPoint = event.pos()
        self.isSelecting = True

    def mouseMoveEvent(self, event):
        if self.isSelecting:
            self.endPoint = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.isSelecting = False
        self.endPoint = event.pos()
        self.closed.emit() 
        self.close()

    def paintEvent(self, event):
        if self.startPoint and self.endPoint:
            qp = QPainter(self)
            qp.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine))
            rect = QRect(self.startPoint, self.endPoint)
            qp.drawRect(rect)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    selector = RegionSelector()
    selector.show()
    sys.exit(app.exec())