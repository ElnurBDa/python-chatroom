import asyncio
from utils import *
from enum import Enum

class Options(Enum):
    CREATE = 1
    SELECT = 2

clients = {} # {'id': {'name':"bob", 'writer':<writer>, 'chatroom_id':"1"}}
chatrooms = {
    'chat______default_id_of_default_chatroom':"test"
} # {'chatroom_id': 'chatroom_name'}
header = 1024
ip, port = '', 1234

async def send_message(writer, message):
    writer.write(message.encode())
    await writer.drain()

class Client:
    def __init__(self, writer="", reader=""):
        self.id = generate_secure_user_id()
        self.writer = writer
        self.reader = reader
        self.name = ""
        self.chatroom_id = ""
        self.client_address = writer.get_extra_info('peername')
        print(f"New connection from {self.client_address}")

    def get_user_profile(self):
        return {'name': self.name, 'chatroom_id': self.chatroom_id, 'writer': self.writer}

    async def broadcast_to_all(self, message):
        for user_id, values in clients.items():
            if user_id != self.id:
                await send_message(values['writer'],f"{message}")
    
    async def multicast_to_chat(self, message):        
        for user_id, values in clients.items():
            if user_id != self.id and values['chatroom_id'] == self.chatroom_id:
                await send_message(values['writer'],f"{message}")

    async def send_message(self, message):
        self.writer.write(message.encode())
        await self.writer.drain()

    async def receive_message(self):
        data = await self.reader.read(header)
        return data.decode().strip() 

    async def client_req_and_res(self, message):
        await self.send_message(message)
        return await self.receive_message()

    async def remove_client(self):        
        del clients[self.name]
        await self.multicast_to_chat(f"{self.name} has left the chat!\n")
        self.writer.close()
        await self.writer.wait_closed()
        print(f"Connection closed for {self.client_address}")

    async def choose_name(self):
        self.name = await self.client_req_and_res("Welcome to the chatroom! Please enter your name: \n")
        print(f"{self.name} has joined the server")

    async def choose_chat(self):
        option = ""
        while option not in [Options.CREATE, Options.SELECT]:
            chatroom_names = "\n".join(chatrooms.values())
            option = await self.client_req_and_res(f"\n1. Create a Chatroom\n2. Select a Chatroom:\n{chatroom_names}\n")
            try:
                option = Options(int(option))  # Convert user input to enum
            except ValueError:
                option = None
            print(f"{option} is chosen")
        while True:
            if option == Options.CREATE: 
                chatroom_name = await self.client_req_and_res("Enter name of a new chatroom: ")
                print(f"{chatroom_name} chatroom is created")
                self.chatroom_id = generate_secure_chat_id() 
                chatrooms[self.chatroom_id] = chatroom_name
                break
            elif option == Options.SELECT:
                chatroom_name = await self.client_req_and_res("Enter name of a chatroom: ")
                self.chatroom_id = find_id_by_name(chatroom_name, chatrooms)
                if not self.chatroom_id: continue
                break
        await self.multicast_to_chat(f"\n{self.name} has joined the chat!\n")
        print(f"{self.chatroom_id} chatroom is touched in the server")

    async def chat_with_others_in_room(self):
        while True:
            data = await self.reader.read(header)
            if data == b'\r\n': continue # to skip empty messages
            message = f"{self.name}| {data.decode()}"
            await self.multicast_to_chat(message)

async def handle_client(reader, writer):
    client = Client(writer, reader)
    await client.choose_name()
    await client.choose_chat()
    clients[client.id] = client.get_user_profile()
    try:
        await client.chat_with_others_in_room()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error handling client {client.name}: {e}")
    finally:
        await client.remove_client()
        del client

async def main():
    server = await asyncio.start_server(handle_client, ip, port)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
