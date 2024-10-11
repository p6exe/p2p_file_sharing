import socket
import select
import os

'''
commands the server takes:

Assume both the server and user have the same Host address but different Ports
Each user enters their own port whent ehy register with the server

tasks:

Server side:
establish one connection                            - completed
establish multiple connects                         - completed
communication/commands between server and client    - implementing alongside other commands
receive file/registers a file                       - completed
monitor the distribution of chunks                  - something something something
send the user the list of peers                     - completed
integrity checks

User side:
establish connection with server            - completed
get list of peers to download from server   - completed
establish connection with multiple peers    -
parallel downloading with multiple peers    -
'''


HOST = '127.0.0.1'  # Localhost
PORT = 58008        # Port 

class File:
    def __init__(self, file_name, file_size, client_port):
        self.file_name = file_name
        self.file_size = file_size
        self.chunks = {} #{chunk_num, [client_port]}

        self.num_of_chunks = 0
        if (file_size % DEFAULT_CHUNK_SIZE == 0):
            self.num_of_chunks = file_size // DEFAULT_CHUNK_SIZE
        else:
            self.num_of_chunks = file_size // DEFAULT_CHUNK_SIZE + 1

        for i in range(self.num_of_chunks):
            self.chunks[i] = []
        self.file_debug()

    def register_new_client(self, client_port):
        for i in range(self.num_of_chunks):
            #self.chunks[i] = [client_port]
            self.chunks[i].append(client_port)
        self.file_debug()

    def chunk_register(self, client_port, chunk_num):
        self.chunks[chunk_num].append(client_port)
        self.file_debug()

    def get_file_locations(self):
        file_locations = []
        for chunk in self.chunks:
            file_locations.append(self.chunks[chunk][0])
        return file_locations
    
    def get_num_of_chunks(self):
        return self.num_of_chunks

    def remove_user_from_chunk(self, userport):
        for chunk in self.chunks:
            if(userport in self.chunks[chunk]):
                self.chunks[chunk].remove(userport)
        print("removing port addres: ", userport)
        self.file_debug()

    def file_debug(self):
        print("file_name: ", self.file_name, "file_size: ", self.file_size)
        print("chunks: ", self.chunks)


send_buffer = {}    # Buffers that stores the sockets that need a reply after they request
sockets_list = []   # List of all sockets (including server socket)
files = {}          # List of files {file name : file object}
DEFAULT_CHUNK_SIZE = 4096
busy_socket_recv = []

#Dictionary to store multiple addresses
client_addresses = {} # {socket : addr}
client_ports = {} #{socket : port}


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
        
        message = data.decode('utf-8')
        #takes in commands from the user:
        if(message == "register"):
            #filename = client_socket.recv(1024)
            register(client_socket)
        elif(message == "chunk register"):
            #filename = client_socket.recv(1024)
            chunk_register(client_socket)
        #closes
        elif(message == "close"):
            close_socket(client_socket)
        elif(message == "file list"):
            send_list_of_files(client_socket)
        elif(message == "file location"):
            file_name = client_socket.recv(1024).decode('utf-8')
            send_file_location(client_socket, file_name)
        elif(message == "download"):
            file_name = client_socket.recv(1024).decode('utf-8')
            send_download_info(client_socket, file_name)
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


def register(client_socket):
    file_name = (client_socket.recv(1024)).decode('utf-8')                  #recvs filename
    send_confirmation(client_socket)
    file_size = int.from_bytes(client_socket.recv(1024), byteorder='big')   #file size
    client_port = int.from_bytes(client_socket.recv(1024), byteorder='big') #the port of the client

    client_ports[client_socket] = client_port
    #register new file or adds the user as a file holder
    if file_name in files:
        files[file_name].register_new_client(client_port)
    else:
        newfile = File(file_name, file_size, client_port)
        newfile.register_new_client(client_port)
        files[file_name] = newfile
        print("New file: ", file_name)

def chunk_register(client_socket):
    file_name = (client_socket.recv(1024)).decode('utf-8')                  #recvs filename
    send_confirmation(client_socket)
    chunk_num = int.from_bytes(client_socket.recv(8), byteorder='big')
    file_size = int.from_bytes(client_socket.recv(8), byteorder='big')   #file size
    client_port = int.from_bytes(client_socket.recv(8), byteorder='big') #the port of the client

    client_ports[client_socket] = client_port
    #register new file or adds the user as a file holder
    if file_name in files:
        files[file_name].chunk_register(client_port, chunk_num)
    else:
        newfile = File(file_name, file_size, client_port)
        newfile.chunk_register(client_port)
        files[file_name] = newfile
        print("New file: ", file_name)

#sends the user the info of where to get download from
def send_download_info(client_socket, file_name):
    client_socket.sendall(DEFAULT_CHUNK_SIZE.to_bytes(8, byteorder='big'))
    num_of_chunks = files[file_name].get_num_of_chunks()
    client_socket.sendall(num_of_chunks.to_bytes(8, byteorder='big'))
    print(f"download info sent to {client_addresses[client_socket]}")

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

        #chunks = split_file_into_chunks(file_name, DEFAULT_CHUNK_SIZE)
        newfile = File(file_name, file_size, client_addresses[client_socket])
        files[file_name] = newfile
    else:
        print(f"Error: received only {received_size}/{file_size} bytes")


def send_file_location(client_socket, file_name):

    #check if its in the archived file
    if (file_name in files):
        file_locations = files[file_name].get_file_locations()

        #converts the integers to strings
        str_list = []
        for num in file_locations:
            str_list.append(str(num))

        data_list = ','.join(str_list)
        client_socket.sendall(data_list.encode('utf-8'))
        print("Sending location")
    else:               #no files with this name exists
        client_socket.sendall("NULL".encode('utf-8'))
        print("Not a valid file name")

        

def send_list_of_files(client_socket):
    file_list = list(files.keys())
    data_list = ','.join(file_list)
    data = data_list.encode('utf-8')
    client_socket.sendall(data)


#send the file to a user if there are no peers that contain the file
def send_chunk(client_socket, file_name):
    with open(file_name, 'rb') as file:
        file_size = os.path.getsize(file_name)
        while sent_size < file_size:
            remaining_size = file_size - sent_size
            chunk_size = min(1024, remaining_size)
            chunk = client_socket.sendall(chunk_size)
            
            if not chunk:  #Connection closed before the expected file size
                break

            sent_size += len(chunk)

            print(f"Received {file_size}/{file_size} bytes")


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

    #remove the address from all files
    if client_socket in client_ports:
        for file_name in files:
            files[file_name].remove_user_from_chunk(client_ports[client_socket])

    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    print(f"Client {client_addresses[client_socket]} disconnected")
    sockets_list.remove(client_socket)
    del client_addresses[client_socket]


def send_confirmation(client_socket):
    client_socket.sendall("confirm".encode('utf-8'))


def debugger(client_socket):
    print(sockets_list)
    print("using ", client_socket)


if __name__ == '__main__':
    start_server()