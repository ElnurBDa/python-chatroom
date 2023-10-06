import socket
import sys
import threading

class MySocket:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('127.0.0.1', 1234))

    def send_message(self, message):
        self.sock.send(message.encode())

    def receive_message(self):
        data = self.sock.recv(1024)
        return data.decode().strip()

    def send_messages(self):
        while True:
            message = input()
            self.send_message(message)

    def receive_messages(self):
        while True:
            message = self.receive_message()
            print(message)

def main():
    mysocket = MySocket()
    receiver = threading.Thread(target=mysocket.receive_messages)
    receiver.start()
    try:
        mysocket.send_messages()
    except KeyboardInterrupt:
        print("Connection closed by user.")
    finally:
        mysocket.sock.close()

if __name__ == "__main__":
    main()
