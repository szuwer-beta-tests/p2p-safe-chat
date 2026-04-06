import paho.mqtt.client as mqtt
from PyQt6.QtCore import QThread, pyqtSignal
from utils import decrypt_message, encrypt_message
import time
import uuid

BROKER = "broker.hivemq.com"
PORT = 1883

class Host(QThread):
    message_received = pyqtSignal(str, str)
    client_connected = pyqtSignal(str)
    client_disconnected = pyqtSignal(str)

    def __init__(self, room_id):
        super().__init__()
        self.room_id = room_id
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"host_{uuid.uuid4().hex}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.running = False
        self.port = 0

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.client.subscribe(f"chat/{self.room_id}/in")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode('utf-8')
        if payload.startswith("SYS_CONNECT"):
            self.client_connected.emit("Client")
        elif payload.startswith("SYS_DISCONNECT"):
            self.client_disconnected.emit("Client")
        else:
            decrypted = decrypt_message(payload)
            if "|" in decrypted:
                username, msg_txt = decrypted.split("|", 1)
                self.message_received.emit(username, msg_txt)
                self.broadcast(decrypted, echo=False)

    def run(self):
        self.running = True
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
            while self.running:
                time.sleep(0.5)
        except Exception as e:
            print(f"Host error: {e}")
            self.running = False

    def broadcast(self, message, echo=True):
        enc_msg = encrypt_message(message)
        self.client.publish(f"chat/{self.room_id}/out", enc_msg)

    def stop(self):
        self.running = False
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except:
            pass
        self.quit()
        self.wait()

class Client(QThread):
    message_received = pyqtSignal(str, str)
    connection_successful = pyqtSignal()
    connection_failed = pyqtSignal(str)
    disconnected = pyqtSignal()

    def __init__(self, room_id):
        super().__init__()
        self.room_id = room_id
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"client_{uuid.uuid4().hex}")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.running = False

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.client.subscribe(f"chat/{self.room_id}/out")
            self.client.publish(f"chat/{self.room_id}/in", "SYS_CONNECT")
            self.connection_successful.emit()
            self.running = True
        else:
            self.connection_failed.emit(f"Refused: {reason_code}")

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.running = False
        self.disconnected.emit()

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode('utf-8')
        decrypted = decrypt_message(payload)
        if "|" in decrypted:
            username, msg_txt = decrypted.split("|", 1)
            self.message_received.emit(username, msg_txt)

    def run(self):
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
            wait_count = 0
            while not self.running and wait_count < 10:
                time.sleep(0.5)
                wait_count += 1
            if not self.running:
                self.connection_failed.emit("Timeout")
                return
            while self.running:
                time.sleep(0.5)
        except Exception as e:
            if not self.running:
                pass
            else:
                self.connection_failed.emit(str(e))
        finally:
            self.running = False
            self.disconnected.emit()

    def send_message(self, message):
        if self.running:
            try:
                enc_msg = encrypt_message(message)
                self.client.publish(f"chat/{self.room_id}/in", enc_msg)
            except Exception as e:
                print(f"Send failed: {e}")

    def stop(self):
        self.running = False
        try:
            self.client.publish(f"chat/{self.room_id}/in", "SYS_DISCONNECT")
            self.client.loop_stop()
            self.client.disconnect()
        except:
            pass
        self.quit()
        self.wait()
