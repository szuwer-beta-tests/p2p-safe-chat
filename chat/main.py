import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from gui import ModernChatApp

def exception_hook(exctype, value, tb):
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    print("UNCAUGHT EXCEPTION:", error_msg)
    
    # Try to spawn a message box to show the error
    try:
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Debugger - Uncaught Exception")
        msg_box.setText("An error occurred during execution.")
        msg_box.setDetailedText(error_msg)
        msg_box.setStyleSheet("QLabel{min-width: 400px;}") # Make it decently sized
        msg_box.exec()
    except:
        pass
        
sys.excepthook = exception_hook

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = ModernChatApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
