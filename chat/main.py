import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from gui import ChatApp

def exception_hook(exctype, value, tb):
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    print(error_msg)
    try:
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Error")
        msg_box.setText("Something went wrong.")
        msg_box.setDetailedText(error_msg)
        msg_box.setStyleSheet("QLabel{min-width: 400px;}")
        msg_box.exec()
    except:
        pass

sys.excepthook = exception_hook

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ChatApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
