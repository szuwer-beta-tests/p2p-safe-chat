import socket
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from utils import decrypt_message, encrypt_message

class ChatServer(QThread):
    # Signals for GUI updates
    message_received = pyqtSignal(str, str) # username, message
    client_connected = pyqtSignal(str) # address string
    client_disconnected = pyqtSignal(str)

    def __init__(self, port=0):
        super().__init__()
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.port = self.server_socket.getsockname()[1]
        self.clients = [] # List of client sockets
        self.running = True

    def run(self):
        self.server_socket.listen(5)
        while self.running:
            try:
                # Set a timeout so we can periodically check self.running
                self.server_socket.settimeout(1.0)
                client_sock, addr = self.server_socket.accept()
                self.clients.append(client_sock)
                addr_str = f"{addr[0]}:{addr[1]}"
                self.client_connected.emit(addr_str)
                
                # Start a thread to handle this client
                handler = threading.Thread(target=self.handle_client, args=(client_sock, addr_str))
                handler.daemon = True
                handler.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Server accept error: {e}")
                break
        
        self.server_socket.close()

    def handle_client(self, client_sock, addr_str):
        while self.running:
            try:
                data = client_sock.recv(4096)
                if not data:
                    break # Client disconnected
                
                decoded_data = data.decode('utf-8')
                # Message format simple: "Username|Message"
                # Since we encrypt, we decrypt first
                decrypted = decrypt_message(decoded_data)
                if "|" in decrypted:
                    username, msg = decrypted.split("|", 1)
                    self.message_received.emit(username, msg)
                    self.broadcast(decrypted, sender_sock=client_sock)
            except Exception as e:
                break
        
        # Cleanup on disconnect
        if client_sock in self.clients:
            self.clients.remove(client_sock)
        try:
            client_sock.close()
        except:
            pass
        self.client_disconnected.emit(addr_str)

    def broadcast(self, message: str, sender_sock=None):
        """Send message to all clients. Used by host to send to everyone, and to relay."""
        enc_msg = encrypt_message(message).encode('utf-8')
        for client in self.clients:
            if client != sender_sock:
                try:
                    client.sendall(enc_msg)
                except Exception:
                    pass

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class ChatClient(QThread):
    message_received = pyqtSignal(str, str) # username, message
    connection_successful = pyqtSignal()
    connection_failed = pyqtSignal(str)
    disconnected = pyqtSignal()

    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def run(self):
        try:
            self.client_socket.connect((self.ip, self.port))
            self.running = True
            self.connection_successful.emit()
            
            while self.running:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                
                decoded_data = data.decode('utf-8')
                decrypted = decrypt_message(decoded_data)
                if "|" in decrypted:
                    username, msg = decrypted.split("|", 1)
                    self.message_received.emit(username, msg)

        except Exception as e:
            if not self.running:
                pass # Expected disconnect
            else:
                self.connection_failed.emit(str(e))
        finally:
            self.running = False
            self.disconnected.emit()
            try:
                self.client_socket.close()
            except:
                pass
                
    def send_message(self, message: str):
        if self.running:
            try:
                enc_msg = encrypt_message(message).encode('utf-8')
                self.client_socket.sendall(enc_msg)
            except Exception as e:
                print(f"Failed to send message: {e}")

    def stop(self):
        self.running = False
        try:
            self.client_socket.close()
        except:
            pass
        self.quit()
        self.wait()
