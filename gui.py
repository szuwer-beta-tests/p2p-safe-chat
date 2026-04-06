import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLineEdit, QLabel, QMessageBox, QScrollArea, QFrame,
    QListWidget, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPalette

from utils import generate_invite_code, decode_invite_code, load_app_data, save_app_data, get_hashed_mac
from network import ChatServer, ChatClient

class ChatStyle:
    BG_COLOR = "#121212"
    PANEL_COLOR = "#1E1E1E"
    TEXT_COLOR = "#E0E0E0"
    ACCENT_COLOR = "#BB86FC"
    BUBBLE_ME = "#3700B3"
    BUBBLE_THEM = "#2C2C2C"

class ModernChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secure P2P Chat")
        self.resize(900, 600)
        
        self.server = None
        self.client = None
        self.username = f"User{id(self) % 10000:04d}"
        self.role = None
        
        self.app_data = load_app_data()
        self.current_chat_id = None

        self.setup_ui()

    def setup_ui(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(ChatStyle.BG_COLOR))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(ChatStyle.TEXT_COLOR))
        palette.setColor(QPalette.ColorRole.Base, QColor(ChatStyle.PANEL_COLOR))
        palette.setColor(QPalette.ColorRole.Text, QColor(ChatStyle.TEXT_COLOR))
        self.setPalette(palette)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main Horizontal Layout
        main_h_layout = QHBoxLayout(main_widget)
        main_h_layout.setContentsMargins(15, 15, 15, 15)
        main_h_layout.setSpacing(15)
        
        # --- Sidebar ---
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(10)
        
        lbl_contacts = QLabel("Saved Contacts")
        lbl_contacts.setStyleSheet(f"color: {ChatStyle.ACCENT_COLOR}; font-weight: bold; font-size: 14px;")
        sidebar_layout.addWidget(lbl_contacts)
        
        self.contact_list = QListWidget()
        self.contact_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {ChatStyle.PANEL_COLOR};
                color: {ChatStyle.TEXT_COLOR};
                border-radius: 5px;
                border: 1px solid #333333;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid #333333;
            }}
            QListWidget::item:selected {{
                background-color: {ChatStyle.ACCENT_COLOR};
                color: white;
            }}
        """)
        self.contact_list.itemClicked.connect(self.on_contact_selected)
        sidebar_layout.addWidget(self.contact_list)
        
        # Button to add current connection as contact
        self.btn_save_contact = self.create_button("Save Current", ChatStyle.PANEL_COLOR)
        self.btn_save_contact.clicked.connect(self.save_current_contact)
        self.btn_save_contact.setEnabled(False)
        sidebar_layout.addWidget(self.btn_save_contact)
        
        main_h_layout.addWidget(sidebar_widget)
        
        # --- Chat Area ---
        chat_v_layout = QVBoxLayout()
        chat_v_layout.setContentsMargins(0, 0, 0, 0)
        chat_v_layout.setSpacing(10)

        # Top Bar
        top_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet(f"color: {ChatStyle.TEXT_COLOR}; font-weight: bold;")
        
        self.user_input = QLineEdit()
        self.user_input.setText(self.username)
        self.user_input.setPlaceholderText("Username")
        self.user_input.setFixedWidth(120)
        self.user_input.setStyleSheet(self.get_input_style())
        self.user_input.textChanged.connect(self.update_username)

        self.btn_show_code = self.create_button("Host Chat", ChatStyle.ACCENT_COLOR)
        self.btn_show_code.clicked.connect(self.start_host)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Invite code...")
        self.code_input.setFixedWidth(160)
        self.code_input.setStyleSheet(self.get_input_style())

        self.btn_copy_code = self.create_button("Copy Code", ChatStyle.PANEL_COLOR)
        self.btn_copy_code.clicked.connect(self.copy_invite_code)

        self.btn_connect = self.create_button("Connect", ChatStyle.ACCENT_COLOR)
        self.btn_connect.clicked.connect(self.connect_to_host)

        top_layout.addWidget(self.status_label)
        top_layout.addStretch()
        top_layout.addWidget(self.user_input)
        top_layout.addWidget(self.btn_show_code)
        top_layout.addWidget(self.code_input)
        top_layout.addWidget(self.btn_copy_code)
        top_layout.addWidget(self.btn_connect)
        chat_v_layout.addLayout(top_layout)

        # Chat Area (Scrollable with proper Bubbles)
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet(f"background-color: {ChatStyle.BG_COLOR}; border: none;")
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.chat_scroll.setWidget(self.scroll_content)
        chat_v_layout.addWidget(self.chat_scroll)

        # Input Area
        input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type a message...")
        self.msg_input.setStyleSheet(self.get_input_style())
        self.msg_input.returnPressed.connect(self.send_message)

        self.btn_send = self.create_button("Send", ChatStyle.ACCENT_COLOR)
        self.btn_send.clicked.connect(self.send_message)

        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(self.btn_send)
        chat_v_layout.addLayout(input_layout)
        
        main_h_layout.addLayout(chat_v_layout)
        
        self.refresh_contact_list()

    def get_input_style(self):
        return f"""
            QLineEdit {{
                background-color: {ChatStyle.PANEL_COLOR};
                color: {ChatStyle.TEXT_COLOR};
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ChatStyle.ACCENT_COLOR};
            }}
        """

    def create_button(self, text, bg_color):
        btn = QPushButton(text)
        style = f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #A060F0;
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #888888;
            }}
        """
        btn.setStyleSheet(style)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def update_username(self):
        new_name = self.user_input.text().strip()
        if new_name:
            self.username = new_name

    def copy_invite_code(self):
        code = self.code_input.text().strip()
        if code:
            QApplication.clipboard().setText(code)
            self.update_status("Code Copied!")

    def on_contact_selected(self, item):
        contact_name = item.text()
        for contact in self.app_data.get("contacts", []):
            if contact['name'] == contact_name:
                self.code_input.setText(contact['code'])
                break

    def refresh_contact_list(self):
        self.contact_list.clear()
        for contact in self.app_data.get("contacts", []):
            self.contact_list.addItem(contact['name'])

    def save_current_contact(self):
        if not self.current_chat_id:
            return
        code = self.code_input.text().strip()
        if not code and self.role == 'host':
            # Host saves own link maybe?
            pass
            
        name, ok = QInputDialog.getText(self, "Save Contact", "Enter contact name:")
        if ok and name:
            self.app_data["contacts"].append({"name": name, "code": code, "hash": self.current_chat_id})
            save_app_data(self.app_data)
            self.refresh_contact_list()

    def create_chat_bubble(self, username, message, is_me=False, time_str=None):
        bubble_container = QWidget()
        h_layout = QHBoxLayout(bubble_container)
        h_layout.setContentsMargins(0, 5, 0, 5)
        
        bubble = QFrame()
        bg_color = ChatStyle.BUBBLE_ME if is_me else ChatStyle.BUBBLE_THEM
        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 12px;
            }}
        """)
        
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 10, 12, 10)
        bubble_layout.setSpacing(4)
        
        if not is_me:
            user_lbl = QLabel(username)
            user_lbl.setStyleSheet(f"color: #AAAAAA; font-size: 11px; font-weight: bold;")
            bubble_layout.addWidget(user_lbl)
            
        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(f"color: {ChatStyle.TEXT_COLOR}; font-size: 14px;")
        msg_lbl.setWordWrap(True)
        msg_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # Hardcoding a max width for safety
        msg_lbl.setMaximumWidth(400)
        bubble_layout.addWidget(msg_lbl)
        
        if not time_str:
            time_str = datetime.now().strftime("%H:%M")
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet(f"color: #888888; font-size: 10px;")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        bubble_layout.addWidget(time_lbl)
        
        if is_me:
            h_layout.addStretch()
            h_layout.addWidget(bubble)
        else:
            h_layout.addWidget(bubble)
            h_layout.addStretch()
            
        return bubble_container

    def render_bubble(self, username, message, is_me=False, time_str=None, save_history=True):
        bubble = self.create_chat_bubble(username, message, is_me, time_str)
        self.scroll_layout.addWidget(bubble)
        
        if save_history and self.current_chat_id:
            if not time_str:
                time_str = datetime.now().strftime("%H:%M")
            if self.current_chat_id not in self.app_data["history"]:
                self.app_data["history"][self.current_chat_id] = []
            
            self.app_data["history"][self.current_chat_id].append({
                "username": username,
                "message": message,
                "is_me": is_me,
                "time_str": time_str
            })
            save_app_data(self.app_data)
        
        # Auto scroll to bottom
        QApplication.processEvents()
        vbar = self.chat_scroll.verticalScrollBar()
        vbar.setValue(vbar.maximum())
        
    def load_chat_history(self):
        # Clear existing layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        if self.current_chat_id in self.app_data.get("history", {}):
            for msg_data in self.app_data["history"][self.current_chat_id]:
                # render bubble but don't save to history again
                self.render_bubble(
                    msg_data["username"], 
                    msg_data["message"], 
                    msg_data["is_me"], 
                    msg_data.get("time_str", ""),
                    save_history=False
                )

    def start_host(self):
        if self.server is None and self.client is None:
            self.server = ChatServer(port=0)
            self.server.message_received.connect(self.display_received_message)
            self.server.client_connected.connect(lambda addr: self.update_status(f"Hosted (Client {addr} joined)"))
            self.server.client_disconnected.connect(lambda addr: self.update_status(f"Hosted (Client {addr} left)"))
            self.server.start()
            self.role = 'host'
            self.current_chat_id = get_hashed_mac() # Host's chat id is their own hash
            self.load_chat_history()
            
            self.update_status("Hosting (Waiting for connection...)")
            
            code = generate_invite_code(self.server.port)
            self.btn_show_code.setEnabled(False)
            self.btn_connect.setEnabled(False)
            self.code_input.setText(code)
            self.btn_save_contact.setEnabled(True)
            self.btn_copy_code.setEnabled(True)
        else:
            QMessageBox.warning(self, "Warning", "Already connected or hosting.")

    def connect_to_host(self):
        if self.server is None and self.client is None:
            code = self.code_input.text().strip()
            if not code:
                QMessageBox.warning(self, "Notice", "Please paste an invite code in the input field.")
                return

            ip, port, chat_hash = decode_invite_code(code)
            if ip and port:
                self.client = ChatClient(ip, port)
                self.client.message_received.connect(self.display_received_message)
                self.client.connection_successful.connect(self.on_connection_successful)
                self.client.connection_failed.connect(self.connection_failed)
                self.client.disconnected.connect(lambda: self.update_status("Disconnected"))
                self.role = 'client'
                self.current_chat_id = chat_hash
                
                self.client.start()
                self.update_status("Connecting...")
                self.btn_show_code.setEnabled(False)
                self.btn_connect.setEnabled(False)
                self.code_input.setEnabled(False)
            else:
                QMessageBox.warning(self, "Error", "Invalid Invite Code.")
        else:
            QMessageBox.warning(self, "Warning", "Already connected or hosting.")

    def on_connection_successful(self):
        self.update_status("Connected")
        self.btn_save_contact.setEnabled(True)
        self.load_chat_history()

    def connection_failed(self, error_msg):
        self.update_status("Connection Failed")
        QMessageBox.critical(self, "Connection Error", f"Failed to connect:\n{error_msg}")
        self.cleanup_connection()

    def update_status(self, status):
        self.status_label.setText(f"Status: {status}")

    def cleanup_connection(self):
        self.role = None
        self.current_chat_id = None
        self.btn_show_code.setEnabled(True)
        self.btn_connect.setEnabled(True)
        self.code_input.setEnabled(True)
        self.btn_save_contact.setEnabled(False)
        if self.server:
            self.server.stop()
            self.server = None
        if self.client:
            self.client.stop()
            self.client = None
        self.update_status("Disconnected")

    def send_message(self):
        msg = self.msg_input.text().strip()
        if not msg:
            return
            
        full_msg = f"{self.username}|{msg}"
        self.render_bubble(self.username, msg, is_me=True)
        
        # Send to network
        if self.role == 'host' and self.server:
            self.server.broadcast(full_msg)
        elif self.role == 'client' and self.client:
            self.client.send_message(full_msg)
            
        self.msg_input.clear()

    @pyqtSlot(str, str)
    def display_received_message(self, username, msg):
        self.render_bubble(username, msg, is_me=False)

    def closeEvent(self, event):
        self.cleanup_connection()
        super().closeEvent(event)
