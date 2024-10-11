import socket
import select
import os
import hashlib

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

#File class is used to hold information about a file such as name, chunks, and important funcs
class File:
    # contructor initializes values and 
    def __init__(self, file_name, file_size, client_port):
        self.file_name = file_name
        self.file_size = file_size
        self.chunks = {} #{chunk_num: [client_port]}

        self.chunk_hashes = {} #{chunk_num, chunk hash}
        self.num_of_chunks = 0
        if (file_size % DEFAULT_CHUNK_SIZE == 0):
            self.num_of_chunks = file_size // DEFAULT_CHUNK_SIZE
        else:
            self.num_of_chunks = file_size // DEFAULT_CHUNK_SIZE + 1
        # set the files chunks to an empty array so that it can store a list of chunks
        for i in range(self.num_of_chunks):
            self.chunks[i] = []
        self.file_debug() # general purpose output for file and descr. info
        
    def get_hash(self, chunk_num):
        return self.chunk_hashes[chunk_num]
        
    def store_hashes(self, chunk_hashes):
        for i in range(len(chunk_hashes)):
            self.chunk_hashes[i] = chunk_hashes[i]
        print(self.chunk_hashes)
        
    def register_new_client(self, client_port):
        for i in range(self.num_of_chunks):
            #self.chunks[i] = [client_port]
            self.chunks[i].append(client_port)
        self.file_debug()
    #registers a chunk with between client and server
    def chunk_register(self, client_port, chunk_num):
        self.chunks[chunk_num].append(client_port)
        self.file_debug()
    # appends the location of each file to a list.
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

    # outputs the files name size and self.chunks
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

#Send a message to a specific client
def send(client_socket, message):
    try:
        #send message to peer
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
        message = message.strip()
        #takes in commands from the user:
        if(message == "register"):
            #filename = client_socket.recv(1024)
            register(client_socket)
        #closes
        elif(message == "chunk register"):
            #filename = client_socket.recv(1024)
            chunk_register(client_socket)
        elif(message == "close"):
            close_socket(client_socket)
        elif(message == "file list"): #outputs a list of files, the names, and their sizes
            send_list_of_files(client_socket)
        elif(message == "file location"): #outputs a list of where a specified peer can find a file
            file_name = client_socket.recv(1024).decode('utf-8')
            send_file_location(client_socket, file_name)
        elif(message == "store hash"):
            file_name = client_socket.recv(1024).decode('utf-8')
            chunk_hashes = client_socket.recv(1024).decode('utf-8').split(',')
            files[file_name].store_hashes(chunk_hashes)
        elif(message == "verify chunk"):
            send_confirmation(client_socket)
            file_name = client_socket.recv(1024).decode('utf-8')
            chunk_num = int.from_bytes(client_socket.recv(8), byteorder='big')
            print(chunk_num)
            hash = files[file_name].get_hash(chunk_num)
            print(hash)
            client_socket.sendall(hash.encode('utf-8'))
            print("sending verify hash")
        elif(message == "download"): # navigates a peer on where to download a file
            file_name = client_socket.recv(1024).decode('utf-8')
            send_download_info(client_socket, file_name)
        elif message == "chunk selection":  # navigates the rarity element of finding where a peer should download
            file_name = client_socket.recv(1024).decode('utf-8')
            send_download_info(client_socket, file_name)

    except ConnectionError as e:
        #Handle client disconnection
        close_socket(client_socket)
        

# allows a peer to register a file with the network and that peer becomes an endpoint
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

#registers a chunk with the server so a peer can find where to download it from
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
        newfile.chunk_register(client_port, chunk_num)
        files[file_name] = newfile
        print("New file: ", file_name)

#sends the user the info of where to get download from
def send_download_info(client_socket, file_name):
    client_socket.sendall(DEFAULT_CHUNK_SIZE.to_bytes(8, byteorder='big'))
    num_of_chunks = files[file_name].get_num_of_chunks()
    client_socket.sendall(num_of_chunks.to_bytes(8, byteorder='big'))
    print(f"download info sent to {client_addresses[client_socket]}")

#receives a file and creates a reference point for other peers
def receive_file(client_socket, file_name):
    #Receive the file size from the server
    file_size_data = client_socket.recv(8)  #Expecting 8 bytes for file size
    file_size = int.from_bytes(file_size_data, byteorder='big')
    print(f"Receiving file of size: {file_size} bytes")

    #Start receiving the file in chunks
    received_size = 0   #total data received

    with open(file_name, 'wb') as file:
        #stores bytes until all are found
        while received_size < file_size:
            remaining_size = file_size - received_size
            chunk_size = min(1024, remaining_size)
            chunk = client_socket.recv(chunk_size)
            
            if not chunk:  #Connection closed before the expected file size
                break

            file.write(chunk)
            received_size += len(chunk)

            print(f"Received {received_size}/{file_size} bytes")
    #output to the file was received if all bytes are present and add the new file to the files dict.
    if received_size == file_size:
        print(f"File {file_name} received successfully")

        #chunks = split_file_into_chunks(file_name, DEFAULT_CHUNK_SIZE)
        newfile = File(file_name, file_size, client_addresses[client_socket])
        files[file_name] = newfile
    else:
        print(f"Error: received only {received_size}/{file_size} bytes")

#outputs list of where to download a file and the number of endpoints
def send_file_location(client_socket, file_name):

    #check if its in the archived file
    if (file_name in files):
        file_locations = files[file_name].get_file_locations()

        #converts the integers to strings
        str_list = []
        for num in file_locations:
            str_list.append(str(num))

        #join into a string and send to peer
        data_list = ','.join(str_list)
        client_socket.sendall(data_list.encode('utf-8'))
        print("Sending location")
    else:               #no files with this name exists
        client_socket.sendall("NULL".encode('utf-8'))
        print("Not a valid file name")        

#outputs a list of files that can be downloaded from any peer
def send_list_of_files(client_socket):
    #uses keys of files to represent names
    file_list = list(files.keys())
    num_of_files = len(file_list)
    
    out=[f"Number of files: {num_of_files}"] #initial output for number of files
    #adds each file and its size
    for file in file_list:
        out.append(f"File Name: {file} Size of file: {files[file].file_size}")
    
    #join output into a string and sent to peer
    data_list = ';'.join(out)
    data = data_list.encode('utf-8')
    client_socket.sendall(data)

# Send chunk data and hash
def send_chunk(client_socket, file_name, chunk_num):
    file = files[file_name]
    chunk_hash = file.get_chunk_hash(chunk_num)
    
    #access file and read in chunks
    with open(file_name, 'rb') as f:
        f.seek(chunk_num * DEFAULT_CHUNK_SIZE)
        chunk = f.read(DEFAULT_CHUNK_SIZE)
        client_socket.sendall(chunk)  
        client_socket.sendall(chunk_hash.encode('utf-8'))   # send hashed chunk to peer
        print(f"Sent chunk {chunk_num} and hash {chunk_hash} to {client_addresses[client_socket]}")


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


# confirmation message to peer
def send_confirmation(client_socket):
    client_socket.sendall("confirm".encode('utf-8'))


def debugger(client_socket):
    print(sockets_list)
    print("using ", client_socket)

# information relating to chunk selection. Sends data about a peer that owns a file
def send_download_info(client_socket, file_name):
    # Send default chunk size
    client_socket.sendall(DEFAULT_CHUNK_SIZE.to_bytes(8, byteorder='big'))
    #get number of chunks for the file
    num_of_chunks = files[file_name].get_num_of_chunks()
    client_socket.sendall(num_of_chunks.to_bytes(8, byteorder='big'))
    print(f"Download info sent to {client_addresses[client_socket]}")

    # After sending download info, get chunk availability from all clients holding this file
    chunk_availability = files[file_name].get_file_locations()  # Adjust this to retrieve chunk info
    availability_info = f"Chunk availability for {file_name}:"

    # build the availability message
    for chunk_num in range(files[file_name].get_num_of_chunks()):
        peers = files[file_name].chunks[chunk_num]  # Get peers for each chunk
        availability_info += f"\nChunk {chunk_num}: Available from peers: {', '.join(map(str, peers)) if peers else 'None'}"

    #Send the availability information to the client
    client_socket.sendall(availability_info.encode('utf-8'))
    print(f"Sent chunk availability to {client_addresses[client_socket]}: {availability_info}")


if __name__ == '__main__':
    start_server()