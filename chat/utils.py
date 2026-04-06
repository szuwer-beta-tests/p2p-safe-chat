import uuid
import hashlib
import base64
import json
import os

def get_mac():
    mac_num = uuid.getnode()
    return ':'.join(('%012X' % mac_num)[i:i+2] for i in range(0, 12, 2))

def get_hashed_mac():
    return hashlib.sha256(get_mac().encode('utf-8')).hexdigest()[:8]

def get_random_room():
    return os.urandom(8).hex()

def generate_invite_code(room_id):
    data = {"r": room_id, "h": get_hashed_mac()}
    encoded = base64.urlsafe_b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
    return encoded.rstrip('=')

def decode_invite_code(code):
    padding = len(code) % 4
    if padding > 0:
        code += '=' * (4 - padding)
    try:
        data = json.loads(base64.urlsafe_b64decode(code.encode('utf-8')).decode('utf-8'))
        return data.get("r"), data.get("h")
    except Exception:
        return None, None

def encrypt_message(msg):
    return base64.b64encode(msg.encode('utf-8')).decode('utf-8')

def decrypt_message(enc_msg):
    try:
        return base64.b64decode(enc_msg.encode('utf-8')).decode('utf-8')
    except Exception:
        return enc_msg

def load_app_data(file_path='chat_data.json'):
    if not os.path.exists(file_path):
        return {"contacts": [], "history": {}}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "contacts" not in data: data["contacts"] = []
            if "history" not in data: data["history"] = {}
            return data
    except Exception:
        return {"contacts": [], "history": {}}

def save_app_data(data, file_path='chat_data.json'):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass
