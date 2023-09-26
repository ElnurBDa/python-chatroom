import secrets
import hashlib

def generate_secure_user_id():
    # Generate a random 32-byte token using the secrets module
    random_token = secrets.token_bytes(32)

    # Hash the random token using a secure hash function (SHA-256)
    user_id = hashlib.sha256(random_token).hexdigest()

    return user_id

if __name__ == "__main__":
    user_id = generate_secure_user_id()
    print("Secure User ID:", user_id)
