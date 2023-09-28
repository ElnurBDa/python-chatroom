import socket
import threading
import rsa
import time


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
        self.other_clients_in_chat = [] # [{'client_id':"", 'public_key':""}}]

    def send_message(self, message):
        self.sock.send(message.encode())
    
    def send_public_key(self):
        self.sock.send(self.public_key.save_pkcs1())

    def receive_message(self):
        data = self.sock.recv(1024)
        return data.decode().strip()

    def send_messages(self):
        while True:
            message = input()
            if len(self.other_clients_in_chat)>0:
                for n in range(0,len(message),245):
                    part = message[n:n+245]
                    for client in self.other_clients_in_chat:
                        encMessage = rsa.encrypt(part.encode(), rsa.PublicKey.load_pkcs1(client['client_public_key']))
                        part = f"e2em|||{client['client_id']}|||{encMessage}"
                        self.send_message(part)
                        time.sleep(0.1)
                continue
            self.send_message(message)

    def receive_messages(self):
        while True:
            message = self.receive_message()
            client_id = "CHAT"
            num = count_word_occurrences(message, 'e2ek')
            parts = message.strip().split('|||')
            for i in range(num):
                if parts[i*3] == 'e2ek':
                    client_id = parts[1+i*3]
                    client_public_key = parts[2+i*3]
                    client = {
                        'client_id': client_id,
                        'client_public_key': client_public_key
                    }
                    self.other_clients_in_chat.append(client)
                    message = "I joined"
            if parts[0] == 'e2em':
                client_id = parts[1]
                m = eval(f"b{parts[2][1:]}")
                message = str(rsa.decrypt(eval(f"b{parts[2][1:]}"), self.private_key))[2:-1]
            print(f"{client_id} > {message}")

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
