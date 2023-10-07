import socket
import threading
import rsa

# e2ek|||client_id|||public_key
# e2em|||client_id|||encrypted_message


def count_word_occurrences(text, word):
    words = text.strip().split('|||')
    count = 0
    for w in words:
        if w == word:
            count += 1
    return count

class MySocket:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('127.0.0.1', 8888))
        self.public_key, self.private_key = rsa.newkeys(2048)
        self.other_clients_in_chat = {} # {client_id: public_key}

    def send_message(self, message):
        self.sock.send(message.encode())
    
    def send_public_key(self):
        self.sock.send(self.public_key.save_pkcs1())

    def receive_message(self):
        data = self.sock.recv(4096)
        return data.decode().strip()

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
                    print(part)
                    client_id, public_key_encoded = part.split("|||")
                    self.other_clients_in_chat[client_id] = rsa.PublicKey.load_pkcs1(public_key_encoded)
                    # print(f"Client {client_id} with {public_key_encoded} is here!")
            else:
                print(f"<$ {message}") # prints without e2e

def main():
    mysocket = MySocket()
    receiver = threading.Thread(target=mysocket.receive_messages)
    mysocket.send_public_key()
    receiver.start()
    try:
        mysocket.send_messages()
    except KeyboardInterrupt:
        print("Connection closed by user.")
    finally:
        mysocket.sock.close()

if __name__ == "__main__":
    main()
