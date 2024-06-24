import sys
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget
from PyQt6.QtGui import QAction, QIcon, QPainter, QColor, QFont, QFontMetrics
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from get_region import RegionSelector
from PIL import ImageGrab
from ocr_api import ocr_text_paddle, ocr_text_api
import string
import os
import re
import sys
utilities_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utilities')
sys.path.append(utilities_dir)
from text_matcher import TextMatcher

matcher_zh = TextMatcher(file_path="./data/lines_zh.json")
matcher_en = TextMatcher(file_path="./data/lines_en.json")

class SubtitleDisplay(QWidget):
    COLORS = {
        'black': QColor(0, 0, 0),
        'white': QColor(255, 255, 255),
        'red': QColor(255, 0, 0),
        'blue': QColor(0, 0, 255),
        'green': QColor(0, 255, 0),
        'purple': QColor(128, 0, 128),
        'orange': QColor(255, 165, 0),
        'yellow': QColor(255, 255, 0),
    }

    def __init__(self, bbox, text='', color='white', parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.bbox = bbox
        self.text = text
        self.color = SubtitleDisplay.COLORS[color]
        self.font = QFont('Arial', 20)
        self.fontMetrics = QFontMetrics(self.font)
        self.updateGeometry()

    def updateGeometry(self):
        textWidth = self.bbox[2] - self.bbox[0]
        lines = self.fontMetrics.boundingRect(0, 0, textWidth, 1000, Qt.TextFlag.TextWordWrap, self.text).height()
        
        vertical_padding = 0
        
        newY = self.bbox[3] + vertical_padding 
        
        self.setGeometry(self.bbox[0], newY, textWidth, lines + 20)
        self.initUI()

    def initUI(self):
        self.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
        self.show()

    def setText(self, text):
        self.hide()  
        self.text = text
        self.repaint()  
        self.updateGeometry()
        self.update()
        self.show()  

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.font)
        painter.setPen(self.color)
        rect = self.rect()
        painter.drawText(rect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter, self.text)
        painter.end()

class ScreenshotThread(QThread):
    text_ready = pyqtSignal(str)
    def __init__(self, bbox, original_language="zh", target_language="en"):
        super().__init__()
        self.bbox = bbox
        self.last_ocr_text = None
        self.last_original_text = None
        self.original_language = original_language
        self.target_language = target_language
        self.original_matcher = self.get_matcher(original_language)
        self.target_matcher = self.get_matcher(target_language)

    def get_matcher(self, language):
        if language == "zh":
            return matcher_zh
        elif language == "en":
            return matcher_en


    def run(self):
        screenshot = ImageGrab.grab(bbox=self.bbox)
        screenshot.save('./img/screenshot.png')
        ocr_text = ocr_text_paddle('./img/screenshot.png', self.original_language)
        ocr_text = '\n'.join(ocr_text.split('\n')[2:]) 
        text_only_chinese_and_english = re.sub(r'[^a-zA-Z\u4e00-\u9fa5]', '', ocr_text)
        if text_only_chinese_and_english == self.last_ocr_text:
            return
        self.text_only_chinese_and_english = ocr_text
        print(f"OCR text: {ocr_text}")
        if len(text_only_chinese_and_english) >= 3:
            self.process_text(ocr_text)
        else:
            self.text_ready.emit('')  
        
    def get_target_path(self, original_index):
        original_path = self.original_matcher.text_library[original_index]['path']
        language_mapping = {"cn": "chinese(prc)", "en": "english"}
        parts = original_path.split('/')
        parts[0]= language_mapping[self.target_language]
        return '/'.join(parts)

    def process_text(self, text):
        original_text, original_index = self.original_matcher.find_best_match(text)
        if (original_text == self.last_original_text):
            return
        self.last_original_text = original_text
        print(f"Original text: {original_text}")
        if original_index is not None:
            try:
                target_path = self.get_target_path(original_index)
                target_text, _ = self.target_matcher.find_by_path(target_path)
                print(f"Target text: {target_text}")
                if target_text:
                    self.text_ready.emit(target_text)
                else:
                    self.text_ready.emit('')
            except Exception as e:
                print(e)
        else:
            self.text_ready.emit('')

class SystemTrayApp(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.selector = None
        self.screenshot_thread = None
        self.menu = QMenu(parent)
        self.setContextMenu(self.menu)
        self.timer = QTimer()
        self.timer.timeout.connect(self.trigger_screenshot)

        self.select_action = QAction("Select Region", self)
        self.select_action.triggered.connect(self.get_region)
        self.menu.addAction(self.select_action)

        self.start_action = QAction("Start Monitoring", self)
        self.start_action.triggered.connect(self.start_monitoring)
        self.menu.addAction(self.start_action)

        self.pause_action = QAction("Pause Monitoring", self)
        self.pause_action.triggered.connect(self.pause_monitoring)
        self.menu.addAction(self.pause_action)

        self.quit_action = QAction("Quit", self)
        self.quit_action.triggered.connect(QApplication.instance().quit)
        self.menu.addAction(self.quit_action)
        
        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self.open_settings)
        self.menu.addAction(self.settings_action)
        
        self.subtitle_display = None

    def get_region(self):
        self.selector = RegionSelector()
        self.selector.closed.connect(self.create_thread)
        self.selector.show()

    def create_thread(self):
        if self.selector.startPoint and self.selector.endPoint:
            globalStartPoint = self.selector.mapToGlobal(self.selector.startPoint)
            globalEndPoint = self.selector.mapToGlobal(self.selector.endPoint)
            self.bbox = (
                min(globalStartPoint.x(), globalEndPoint.x()), 
                min(globalStartPoint.y(), globalEndPoint.y()), 
                max(globalStartPoint.x(), globalEndPoint.x()), 
                max(globalStartPoint.y(), globalEndPoint.y())
            )
            self.screenshot_thread = ScreenshotThread(self.bbox)
            self.screenshot_thread.text_ready.connect(self.update_subtitle)    

    def trigger_screenshot(self):
        if self.screenshot_thread and not self.screenshot_thread.isRunning():
            self.screenshot_thread.start()

    def start_monitoring(self):
        self.timer.start(100) 

    def pause_monitoring(self):
        self.timer.stop()

    def update_subtitle(self, text):
        if not self.subtitle_display:
            self.subtitle_display = SubtitleDisplay(self.bbox, text)
        else:
            self.subtitle_display.setText(text)
    
    def open_settings(self):
        # TODO: Implement the settings functionality
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    icon_path = os.path.join(os.getcwd(), 'img', 'icon.png')
    trayContainer = SystemTrayApp(QIcon(icon_path))
    trayContainer.setToolTip('Subtitle Tool')
    trayContainer.show()
    sys.exit(app.exec())