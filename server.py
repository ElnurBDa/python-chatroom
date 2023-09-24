import asyncio

clients = {} # {a:[<writer1>, 'chatroom_name'], b:[<writer2>, 'chatroom_name']}
chatrooms = ["test"] 

# sending the messge to other clients
async def broadcast_to_all(writer, message):
    for client in clients.values():
        if client[0] != writer:
            await client_write_drain(client[0], f"{message}")

async def multicast_to_chat(writer, chatroom_name, message):
    for client in clients.values():
        if client[0] != writer and client[1] == chatroom_name:
            await client_write_drain(client[0], f"{message}")

# send and receive message from a client
async def client_write_drain(writer, message):
    writer.write(message.encode())
    await writer.drain()

async def client_read_decode(reader):
    data = await reader.readline()
    return data.decode().strip() 

async def client_req_and_res(reader, writer, message):
    await client_write_drain(writer, message)
    return await client_read_decode(reader)

# some actions with clients
async def remove_client(writer, chatroom_name, name):        
    del clients[name]
    await multicast_to_chat(writer, chatroom_name, f"{name} has left the chat!\n")
    writer.close()
    await writer.wait_closed()

async def choose_chat(reader, writer):
    option = ""
    while option not in ["1", "2"]:
        option = await client_req_and_res(reader, writer, f"\n1. Create a Chatroom\n2. Select a Chatroom {chatrooms}\n")

    chatroom_name = ""
    while True:
        if option == "1": 
            chatroom_name = await client_req_and_res(reader, writer, "Enter name of a new chatroom: ")
            print(f"{chatroom_name} chatroom is created")
            chatrooms.append(chatroom_name)
            break
        elif option == "2":
            chatroom_name = await client_req_and_res(reader, writer, "Enter name of a chatroom: ")
            if chatroom_name not in chatrooms: continue
            break
    return chatroom_name

async def handle_client(reader, writer):
    client_address = writer.get_extra_info('peername')
    print(f"New connection from {client_address}")

    name = await client_req_and_res(reader, writer, "Welcome to the chatroom! Please enter your name: ")
    chatroom_name = await choose_chat(reader, writer)
    clients[name] = [writer, chatroom_name]
    await multicast_to_chat(writer, chatroom_name, f"\n{name} has joined the chat!\n")

    try:
        while True:
            # sending data to others
            data = await reader.readline()
            if data == b'\r\n': continue # to skip empty messages
            message = f"{name}| {data.decode()}"
            await multicast_to_chat(writer, chatroom_name, message)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error handling client {name}: {e}")
    finally:
        await remove_client(writer, chatroom_name, name)
        print(f"Connection closed for {client_address}")

async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
