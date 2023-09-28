import socket
import threading
import rsa

class MySocket:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('127.0.0.1', 8888))
        self.public_key, self.private_key = rsa.newkeys(512)
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
                for client in self.other_clients_in_chat:
                    encMessage = rsa.encrypt(message.encode(), rsa.PublicKey.load_pkcs1(client['client_public_key']))
                    message = f"e2em|||{client['client_id']}|||{encMessage}"
            self.send_message(message)

    def receive_messages(self):
        while True:
            message = self.receive_message()
            parts = message.strip().split('|||')
            if len(parts) == 3 and parts[0] == 'e2ek':
                client_id = parts[1]
                client_public_key = parts[2]
                client = {
                    'client_id': client_id,
                    'client_public_key': client_public_key
                }
                self.other_clients_in_chat.append(client)
            if len(parts) == 3 and parts[0] == 'e2em':
                m = eval(f"b{parts[2][1:]}")
                message = str(rsa.decrypt(eval(f"b{parts[2][1:]}"), self.private_key))[2:-1]
            print(message)

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
