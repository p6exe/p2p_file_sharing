import socket
import select
import threading
import os
import hashlib

HOST = '127.0.0.1'  #The server's hostname or IP address
PORT = 58008        #The port used by the server

file_name = [] #current stores the file name since the file will be stored locally

#established when the user enters the value into the command:
SELFHOST = HOST         #client ip address

files = {}   #{file_name: {chunks}}, file is added when calling register
DEFAULT_CHUNK_SIZE = 4096

#Connects to the server socket
def connect_to_server():
    # Create a socket (TCP/IP)
    close_flag = True
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((HOST, PORT))  # Connect to the server

    print(f"client connecting to server {HOST}:{PORT}")

    # Receive a response from the server
    while(close_flag == True):
        commands = [recv]
        command = input("command: ").lower()

        if(command == "recv"): 
            recv(server_socket)
        elif(command == "send"):
            message = input("message: ")
            send(server_socket, message)
        elif(command == "close"):
            close_client(server_socket)
            close_flag = False
        elif(command == "file list"):
            get_list_of_files(server_socket)
        elif(command == "file location"):
            file_name = input("File name: ")
            get_file_location(server_socket, file_name)
        elif(command == "register"):
            file_name = input("File name: ")
            register(server_socket, file_name)
        elif(command == "chunk register"):
            file_name = input("File name: ")
            chunk_register(server_socket, file_name)
        elif(command == "download"):
            file_name = input("File name: ")
            peer_ports = get_file_location(server_socket, file_name)
            if(peer_ports):
                download_from_peers(server_socket, peer_ports, file_name)
        elif(command == "chunk selection"):
            file_name = input("File name: ")
            chunk_selection(server_socket, file_name)
        else:
            print("type help for commands: ",commands)


#Allow other peers to connect to this user, 
# use a thread
def start_connection(Selfport):
    
    sockets_list = []   # List of all sockets (including server socket)
    socket_addr = {} 
    self_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket
    self_socket.bind((HOST, Selfport))
    self_socket.listen(4)     #Listen for incoming connections
    sockets_list.append(self_socket)
    self_socket.setblocking(False)
    print(f"client starting on {HOST}:{Selfport}")


    #send the specified chunk
    while True:
        readable, writable, exceptional = select.select(sockets_list, sockets_list, sockets_list)
        for current_socket in readable:
            if current_socket == self_socket: #establish new connections

                peer_socket, peer_address = self_socket.accept()
                print(f"Connected by {peer_address}")
                socket_addr[peer_socket] = peer_address

                #Set the client socket to non-blocking and add to monitoring list
                peer_socket.setblocking(True)
                sockets_list.append(peer_socket)

            else:   #recvs the chunk and filename the user wants to download
                chunk_num = int.from_bytes(current_socket.recv(8), byteorder='big')
                file_name = current_socket.recv(1024).decode('utf-8')

                current_socket.sendall(chunk_num.to_bytes(8, byteorder='big'))
                current_socket.sendall(files[file_name][chunk_num])
                sockets_list.remove(current_socket)

                print("Request file: ", file_name, " chunk: ", chunk_num, " from: ", socket_addr[current_socket])

#download from peers
def download_from_peers(server_socket, peer_ports, file_name):
    server_socket.sendall("download".encode('utf-8'))
    server_socket.sendall(file_name.encode('utf-8'))

    recv_buffer = {} #{chunk num: peer socket}
    peer_sockets_list = []
    chunk_size = int.from_bytes(server_socket.recv(8), byteorder='big')
    num_of_chunks = int.from_bytes(server_socket.recv(8), byteorder='big')
    chunks = [None]*num_of_chunks #stores all the chunks downloaded

    print(chunk_size, num_of_chunks)
    
    
    #connect to the peers
    for peer in peer_ports:

        #establishes connection with peers
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect((HOST,peer))
        peer_sockets_list.append(peer_socket)
            

        #sends a request to that peer
        chunk_num = peer_sockets_list.index(peer_socket)

        peer_socket.sendall(chunk_num.to_bytes(8, byteorder='big'))
        peer_socket.sendall(file_name.encode('utf-8'))
        recv_buffer[chunk_num] = peer_socket

        print("sent chunk: ", chunk_num, " request to ", peer)
    
    # Use select to wait for data to be available download in concurrently
    while (recv_buffer):
        readable, writable, exceptional = select.select(peer_sockets_list, [], [])

        #gets the download
        for peer_socket in readable:
            
            chunk_num = int.from_bytes(peer_socket.recv(8), byteorder='big')
            print("recieved chunk: ", chunk_num)
            chunks[chunk_num] = peer_socket.recv(chunk_size)
            recv_buffer.pop(chunk_num)

            peer_sockets_list.remove(peer_socket)
            peer_socket.close()
            
            '''if data:
                print(f"Received data: {data.decode()}")
                peer_sockets_list.remove(peer_socket)
                show_download_progress(chunks)
            else:
                # Peer has closed the connection
                print("Peer closed the connection.")
                peer_sockets_list.remove(peer_socket)
                peer_socket.close()'''
    register(server_socket, file_name)
    #writes a new file
    with open("newfile.txt", 'wb') as file:
        for chunk in chunks:
            file.write(chunk)



def get_list_of_files(server_socket):
    #request to server
    server_socket.sendall("file list".encode('utf-8')) 

    #reply from server
    data = server_socket.recv(1024)
    file_list = data.decode('utf-8').split(';')

    print(f"{file_list}")



def get_file_location(server_socket, file_name):
    #request to server 
    server_socket.sendall("file location".encode('utf-8'))
    server_socket.sendall(file_name.encode('utf-8'))

    #reply from server
    data = server_socket.recv(1024)
    file_locations = data.decode('utf-8').split(',')

    if (file_locations[0] == "NULL"):
        print("Not a valid file")
        return

    int_list = []
    for num in file_locations:
        int_list.append(int(num))

    print(f"{len(int_list)} endpoints")
    for port in int_list:
        print(f'127.0.0.1:{port}')
        return int_list
    


#registers a file with the server
'''
when a file is registered with the server, the server should give the user a port number
client gives the server:
'''
def register(server_socket, file_name):
    if os.path.exists(file_name):
        file_size = os.path.getsize(file_name)
        Selfport = int(input("User port (0 - 65535): " ))

        server_socket.sendall("register".encode('utf-8'))
        server_socket.sendall(file_name.encode('utf-8'))

        confirmation = server_socket.recv(1024)
        if(not confirmation):
            return
        
        server_socket.sendall(file_size.to_bytes(8, byteorder='big'))
        server_socket.sendall(Selfport.to_bytes(8, byteorder='big'))

        files[file_name] = split_file_into_chunks(file_name, DEFAULT_CHUNK_SIZE)
        #print("files: ", files)

        start_connection(Selfport) #once registered, user now can be connect from other clients

        print(f"File {file_name} registered with the server!")
    else:
        print("File doesn't exist")


def chunk_register(server_socket, file_name):
    if os.path.exists(file_name):
        chunks = split_file_into_chunks(file_name, DEFAULT_CHUNK_SIZE)
        print("num of chunks: ", len(chunks))
        file_size = os.path.getsize(file_name)
        chunk_num = int(input("which chunk to send (len-1): "))
        Selfport = int(input("User port (0 - 65535): " ))
        
        server_socket.sendall("chunk register".encode('utf-8'))
        server_socket.sendall(file_name.encode('utf-8'))

        confirmation = server_socket.recv(1024)
        if(not confirmation):
            return
    
        server_socket.sendall(chunk_num.to_bytes(8, byteorder='big'))
        server_socket.sendall(file_size.to_bytes(8, byteorder='big'))
        server_socket.sendall(Selfport.to_bytes(8, byteorder='big'))

        if(file_name in files):
            if(chunks[chunk_num] not in files[file_name]):
                files[file_name].append(chunks[chunk_num])
        else:
            files[file_name]= chunks[chunk_num]
        
            
        #print("files: ", files)

        start_connection(Selfport) #once registered, user now can be connect from other clients

        print(f"File {file_name} registered with the server!")
    else:
        print("File doesn't exist")

# helper func to verify the hash of the downloaded chunk
def verify_chunk(chunk_data, expected_hash):
    received_hash = hashlib.sha256(chunk_data).hexdigest()
    return received_hash == expected_hash

# Downloads a chunk and uses the helper to verify
def download_and_verify_chunk(peer_socket, file_name, chunk_num):
    chunk = peer_socket.recv(DEFAULT_CHUNK_SIZE)  # Receive chunk data
    chunk_hash = peer_socket.recv(64).decode('utf-8')  # Receive chunk hash (SHA-256 hex is 64 chars)

    # Verify the chunk data
    if verify_chunk(chunk, chunk_hash):
        print(f"Chunk {chunk_num} matches hash")
        # Save the chunk
        with open(file_name, 'ab') as f:
            f.write(chunk)
    else:
        print(f"Chunk {chunk_num} wrong chunk")

def split_file_into_chunks(file_path, chunk_size):
    chunks = []
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:  # If no more data, break
                break
            chunks.append(chunk)
    return chunks

#Send a message to the server
def send(server_socket, message):
    server_socket.sendall(message.encode('utf-8'))  # Send the message encoded


def send_confirmation(client_socket):
    client_socket.sendall("confirm".encode('utf-8'))


#Receive message from server
def recv(server_socket):
    data = server_socket.recv(1024)
    print(f"Received from server: {data.decode('utf-8')}")
    
    if(data.decode('utf-8') == "download chunk"):
        pass
    elif():
        pass
    #send(server_socket, "Message received!")  # Send acknowledgment

#handles closing the client
def close_client(server_socket):
    server_socket.close()
    print("closing")
    
def chunk_selection(server_socket, file_name):
    server_socket.sendall("chunk selection".encode('utf-8'))  # Send request for chunk selection
    server_socket.sendall(file_name.encode('utf-8'))  # Send the filename

    availability_data = server_socket.recv(1024).decode('utf-8')
    if availability_data == "NULL":
        print("No such file exists on the server.")
        return

    # Parse the availability data
    availability = {}
    lines = availability_data.split('\n')
    for line in lines:
        if line:  # Ensure line is not empty
            parts = line.split(':')
            if len(parts) >= 2:  # Check that parts has at least 2 elements
                try:
                    chunk_num = int(parts[0].split()[1])
                    count = int(parts[1].strip().split()[0])
                    availability[chunk_num] = count
                except (ValueError, IndexError):
                    print(f"Invalid format in line: {line}")
            else:
                print(f"Invalid format in line: {line}")

    # Ensure there are available chunks before proceeding
    if not availability:
        print("No chunks available for download.")
        return

    # Select the rarest chunk
    rarest_chunk = min(availability, key=availability.get)
    rarest_chunk_count = availability[rarest_chunk]
    print(f"The rarest chunk is {rarest_chunk} with {rarest_chunk_count} peers holding it.")

    # Now initiate the download process for the rarest chunk
    download_chunk(server_socket, file_name, rarest_chunk)

def download_chunk(server_socket, file_name, chunk_num):
    # Here you would send a request to the server or relevant peer to download the specified chunk
    print(f"Downloading chunk {chunk_num} of file {file_name}.")
    # Implement the download logic as needed

if __name__ == '__main__':
    connect_to_server()