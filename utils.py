import socket
import uuid
import hashlib
import base64
import json
def get_mac_address() -> str:
    mac_num = uuid.getnode()
    return ':'.join(('%012X' % mac_num)[i:i+2] for i in range(0, 12, 2))
def get_hashed_mac() -> str:
    mac = get_mac_address()
    sha = hashlib.sha256(mac.encode('utf-8')).hexdigest()
    return sha[:8]                                           
def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip
def generate_invite_code(port: int) -> str:
    ip = get_local_ip()
    mac_hash = get_hashed_mac()
    data = {
        "i": ip,
        "p": port,
        "h": mac_hash                                               
    }
    json_str = json.dumps(data)
    encoded = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
    encoded = encoded.rstrip('=')
    return encoded
def decode_invite_code(code: str) -> tuple:
    padding = len(code) % 4
    if padding > 0:
        code += '=' * (4 - padding)
    try:
        decoded_bytes = base64.urlsafe_b64decode(code.encode('utf-8'))
        decoded_str = decoded_bytes.decode('utf-8')
        data = json.loads(decoded_str)
        return data.get("i"), data.get("p"), data.get("h")
    except Exception as e:
        print(f"Failed to decode invite code: {e}")
        return None, None, None
def encrypt_message(msg: str) -> str:
    return base64.b64encode(msg.encode('utf-8')).decode('utf-8')
def decrypt_message(enc_msg: str) -> str:
    try:
        return base64.b64decode(enc_msg.encode('utf-8')).decode('utf-8')
    except Exception:
        return enc_msg
def load_app_data(file_path='chat_data.json'):
    import os
    if not os.path.exists(file_path):
        return {"contacts": [], "history": {}}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "contacts" not in data: data["contacts"] = []
            if "history" not in data: data["history"] = {}
            return data
    except Exception as e:
        print(f"Error loading app data: {e}")
        return {"contacts": [], "history": {}}
def save_app_data(data, file_path='chat_data.json'):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving app data: {e}")
