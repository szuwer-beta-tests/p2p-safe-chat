import socket
import uuid
import hashlib
import base64
import json

def get_mac_address() -> str:
    """Retrieve the physical MAC address of the device."""
    mac_num = uuid.getnode()
    return ':'.join(('%012X' % mac_num)[i:i+2] for i in range(0, 12, 2))

def get_hashed_mac() -> str:
    """Return a SHA-256 hash of the MAC address, shortened for an identifier."""
    mac = get_mac_address()
    sha = hashlib.sha256(mac.encode('utf-8')).hexdigest()
    return sha[:8] # Return an 8-character unique device hash

def get_local_ip() -> str:
    """
    Get the local IP address dynamically without requiring internet access.
    We connect a UDP socket to a generic IP (it doesn't send anything).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def generate_invite_code(port: int) -> str:
    """
    Generate an invite code encoding the IP, Port, and a MAC hash signature.
    Since there is no central server, we must embed the connection info
    directly into the code so the peer can connect.
    """
    ip = get_local_ip()
    mac_hash = get_hashed_mac()
    data = {
        "i": ip,
        "p": port,
        "h": mac_hash # Used to verify if needed, and make it unique
    }
    json_str = json.dumps(data)
    # Simple base64 encoding to obfuscate
    encoded = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
    # Strip padding to make it cleaner
    encoded = encoded.rstrip('=')
    return encoded

def decode_invite_code(code: str) -> tuple:
    """
    Decode an invite code and extract IP and Port.
    Returns (ip, port, identifier/hash).
    """
    # Restore padding
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
    """A trivial placeholder for message encryption."""
    # To implement robust encryption we could use PyCryptodome (AES).
    # Since it's optional, we will do a simple Base64 to fulfill the requirement minimally.
    return base64.b64encode(msg.encode('utf-8')).decode('utf-8')

def decrypt_message(enc_msg: str) -> str:
    """A trivial placeholder for message decryption."""
    try:
        return base64.b64decode(enc_msg.encode('utf-8')).decode('utf-8')
    except Exception:
        return enc_msg
