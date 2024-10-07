import socket
import select
import os

'''
commands the server takes:

Questions:
should the user be able to communicate with the server while its sending a file?

tasks:

Server side:
establish one connection        - completed
establish multiple connects     - completed
communication/commands between server and client - adding necessary commands to client and server
receive file                    - completed
break up a file                 - split implemented
monitor the distribution of chunks
send the user the list of peers
integrity checks

User side:
establish connection with server            - completed
get list of peers to download from server   -
establish connection with multiple peers    -
parallel downloading                        -
'''

'''class file:
    def __init__(self, filename, addr):
        self.filename # will also be the object name
        self.length = '''

HOST = '127.0.0.1'  # Localhost
PORT = 58008        # Port 

default_chunk_size
class File:
    def __init__(self, file_name, file_length, chunks = []):
        self.file_name = file_name
        self.file_length = file_length
        self.chunks = chunks
        self.chunk_orders = {}
        
send_buffer = {}    # Buffers that stores the sockets that need a reply after they request
sockets_list = []   # List of all sockets (including server socket)
file_holders = {}   # stores the files and their respective holders of the chunks e.g. {file : {peers: list of chunks[]}}
file_length = {}    # {file: file length}
files = []          # List of files
DEFAULT_CHUNK_SIZE = 4096
busy_socket_recv = []
#Dictionary to store multiple addresses
client_addresses = {}


#Start the server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket
    server_socket.bind((HOST, PORT))  #Bind the socket to the host and port
    server_socket.listen(4)     #Listen for incoming connections
    server_socket.setblocking(False)
    sockets_list.append(server_socket)
    print(f"Server started on {HOST}:{PORT}")

    #using select to manage the sockets
    while True:
        readable, writable, exceptional = select.select(sockets_list, sockets_list, sockets_list)

        #Handle readable sockets
        for current_socket in readable:
            if current_socket == server_socket: #establish new connections

                client_socket, client_address = server_socket.accept()
                print(f"Connected by {client_address}")
                
                #Set the client socket to non-blocking and add to monitoring list
                client_addresses[client_socket] = client_address
                client_socket.setblocking(True)                                  #doesn't work
                sockets_list.append(client_socket)
                
            else: #Receive data
                recv(current_socket)
                
        #Handle Writable sockets
        for current_socket in writable:
            if(current_socket in send_buffer):
                send(current_socket, "hello")

''' might delete later 
#Create a socket
def create_socket(server_socket):
    client_socket = 0
    client_socket, client_address = server_socket.accept()  # Accept a new connection
    client_addresses[client_address] = client_socket  # Store client in the dictionary
    print(f"Connected by {client_address}")

    send(client_socket, "hello")
'''

#Send a message to a specific client
def send(client_socket, message):
    try:
        print(client_socket)
        client_socket.sendall(message.encode('utf-8'))
        print(f"sent to {client_addresses[client_socket]}: {message}")

        if client_socket in send_buffer:
            del send_buffer[client_socket]
        
    except ConnectionError as e:
        close_socket(client_socket)

#Receive commands from the client
def recv(client_socket):
    try:
        data = client_socket.recv(1024)
        if data:
            print(f"Received from {client_addresses[client_socket]}: {data.decode('utf-8')}")
        else:
            close_socket(client_socket)
        #takes in commands from the user:
        if(data.decode('utf-8') == "register"):
            #filename = client_socket.recv(1024)
            receive_file(client_socket, file_name = "new_file.txt")
        #closes
        elif(data.decode('utf-8') == "close"):
            close_socket(client_socket)
    except ConnectionError as e:
        #Handle client disconnection
        close_socket(client_socket)
    '''except ConnectionResetError:
        print("Connection reset by client")
        close_socket(client_socket)
    except BrokenPipeError:
        print("Broken pipe: Client disconnected abruptly")
        close_socket(client_socket)
    except OSError as e:
        print(f"OS error: {e}")
        close_socket(client_socket)'''
    
#receives a file
def receive_file(client_socket, file_name):
    #Receive the file size from the server
    file_size_data = client_socket.recv(8)  #Expecting 8 bytes for file size
    file_size = int.from_bytes(file_size_data, byteorder='big')
    print(f"Receiving file of size: {file_size} bytes")

    #Start receiving the file in chunks
    received_size = 0   #total data received

    with open(file_name, 'wb') as file:
        while received_size < file_size:
            remaining_size = file_size - received_size
            chunk_size = min(1024, remaining_size)
            chunk = client_socket.recv(chunk_size)
            
            if not chunk:  #Connection closed before the expected file size
                break

            file.write(chunk)
            received_size += len(chunk)

            print(f"Received {received_size}/{file_size} bytes")

    if received_size == file_size:
        print(f"File {file_name} received successfully")

        chunks = split_file_into_chunks(file_name, DEFAULT_CHUNK_SIZE)
        newfile = File(file_name, file_size, chunks)
        files.append[newfile]
    else:
        print(f"Error: received only {received_size}/{file_size} bytes")

def split_file_into_chunks(file_path, chunk_size):
    chunks = []
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:  # If no more data, break
                break
            chunks.append(chunk)
    return chunks

#Close the server and all client connections
def close_server(server_socket):
    print("Closing server and all client connections.")
    for addr, client_socket in client_addresses.items():
        client_socket.close()  #Close each client socket
    server_socket.close()  #Close the server socket
    print("Server closed.")

#handles closing sockets
def close_socket(client_socket):
    if client_socket in send_buffer:
        del send_buffer[client_socket]
    
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    print(f"Client {client_addresses[client_socket]} disconnected")
    sockets_list.remove(client_socket)
    del client_addresses[client_socket]


def debugger(client_socket):
    print(sockets_list)
    print("using ", client_socket)

def create_distributed_file():
    pass

def distribute_file():
    pass

if __name__ == '__main__':
    start_server()