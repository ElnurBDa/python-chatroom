import secrets
import hashlib

def generate_secure_id():
    random_token = secrets.token_bytes(32)
    id = hashlib.sha256(random_token).hexdigest()
    return id

def generate_secure_user_id():
    return 'user' + generate_secure_id()

def generate_secure_chat_id():
    return 'chat' + generate_secure_id()

def find_id_by_name(name_to_find, data):
    for name_id, name in data.items():
        if name == name_to_find:
            return name_id
    return None  # Return None if the name is not found
