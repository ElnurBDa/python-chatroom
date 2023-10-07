import socket
import threading
import rsa

# e2ek|||client_id|||public_key
# e2em|||client_id|||encrypted_message

class MySocket:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('127.0.0.1', 8888))
        self.public_key, self.private_key = rsa.newkeys(2048)
        self.other_clients_in_chat = {} # {client_id: public_key}
    
    def send_messages(self):
        while True:
            message = input("> ")
            if message.lower() == 'exit': break
            if len(self.other_clients_in_chat) == 0: 
                self.sock.send(message.encode())
            else: # we are in room with other clients 
                for client_id, public_key in self.other_clients_in_chat.items():
                    encrypted_message = rsa.encrypt(message.encode(), public_key)
                    self.sock.send(f"e2em|||{client_id}|||{encrypted_message}".encode())

    def receive_messages(self):
        while True:
            data = self.sock.recv(4096)
            message = data.decode().strip()
            if "e2em|||" in message:
                name, client_id, encrypted_message = message.split("|||")
                decrypted_message = rsa.decrypt(eval(encrypted_message), self.private_key).decode()
                print(f"<# {name[:-4]} >{decrypted_message}") # prints with e2e
            elif "e2ek|||" in message:
                parts = message.split("e2ek|||")
                for part in parts[1:]:
                    client_id, public_key_encoded = part.split("|||")
                    self.other_clients_in_chat[client_id] = rsa.PublicKey.load_pkcs1(public_key_encoded)
            else:
                print(f"<$ {message}") # prints without e2e

def main():
    mysocket = MySocket()
    receiver = threading.Thread(target=mysocket.receive_messages)
    mysocket.sock.send(mysocket.public_key.save_pkcs1()) # send public key 
    receiver.start()
    try:
        mysocket.send_messages()
    except KeyboardInterrupt:
        print("Connection closed by user.")
    finally:
        mysocket.sock.close()

if __name__ == "__main__":
    main()
