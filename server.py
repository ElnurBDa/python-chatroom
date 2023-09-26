import asyncio

clients = {} # {a:[<writer1>, 'chatroom_name'], b:[<writer2>, 'chatroom_name']}
chatrooms = ["test"] 
header = 1024

class Client:
    def __init__(self, writer="", reader=""):
        self.writer = writer
        self.reader = reader
        self.name = ""
        self.chatroom_name = ""
        self.client_address = writer.get_extra_info('peername')
        print(f"New connection from {self.client_address}")

    async def broadcast_to_all(self, message):
        for client in clients.values():
            if client[0] != self.writer:
                await self.send_message(client[0], f"{message}")
    
    async def multicast_to_chat(self, message):
        for client in clients.values():
            other_client = Client(client[0],)
            other_client.chatroom_name = client[1]
            if client[0] != self.writer and client[1] == self.chatroom_name:
                await other_client.send_message(f"{message}")
            del other_client

    async def send_message(self, message):
        print(message)
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
        print(f"{self.name} is joined the server")

    async def choose_chat(self):
        option = ""
        while option not in ["1", "2"]:
            option = await self.client_req_and_res(f"\n1. Create a Chatroom\n2. Select a Chatroom {chatrooms}\n")
            print(f"{option} is choosen")
        while True:
            if option == "1": 
                self.chatroom_name = await self.client_req_and_res("Enter name of a new chatroom: ")
                print(f"{self.chatroom_name} chatroom is created")
                chatrooms.append(self.chatroom_name)
                break
            elif option == "2":
                self.chatroom_name = await self.client_req_and_res("Enter name of a chatroom: ")
                if self.chatroom_name not in chatrooms: continue
                break
        await self.multicast_to_chat(f"\n{self.name} has joined the chat!\n")
        print(f"{self.chatroom_name} is touched the server")

async def handle_client(reader, writer):
    client = Client(writer, reader)
    await client.choose_name()
    await client.choose_chat()
    clients[client.name] = [client.writer, client.chatroom_name]

    try:
        while True:
            data = await client.reader.read(header)
            if data == b'\r\n': continue # to skip empty messages
            message = f"{client.name}| {data.decode()}"
            await client.multicast_to_chat(message)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error handling client {client.name}: {e}")
    finally:
        await client.remove_client()
        del client

async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
