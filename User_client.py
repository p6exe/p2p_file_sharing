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
Selfport = 0
DEFAULT_CHUNK_SIZE = 4096 #const set to 4096 bytes

#Connects to the server socket
def connect_to_server():
    close_flag = True
    # initialize socket to TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((HOST, PORT))  # Connect to the server

    print(f"client connecting to server {HOST}:{PORT}")

    # Receive a response from the server
    while(close_flag == True):
        #takes a comamnd from the user and determines what operation to perform
        commands = ["close","file list","file location","register","chunk register","download"]
        print("Commands: ",commands)

        command = input("command: ").lower()

        if(command == "recv"):  # receieve a message from the server
            recv(server_socket)
        elif(command == "send"): # send a message to the server
            message = input("message: ")
            send(server_socket, message)
        elif(command == "close"): # force close connection
            close_client(server_socket)
            close_flag = False
        elif(command == "file list"): #list all files in the network
            get_list_of_files(server_socket)
        elif(command == "file location"): # find the owners of a file's chunks
            file_name = input("File name: ")
            get_file_location(server_socket, file_name)
        elif(command == "register"): # register a file with the server
            file_name = input("File name: ")
            register(server_socket, file_name)
        elif(command == "chunk register"): # registers a chunk with the server
            file_name = input("File name: ")
            chunk_register(server_socket, file_name)
        elif(command == "download"): # download a chunk from another peer
            file_name = input("File name: ")
            peer_ports = get_file_location(server_socket, file_name)
            if(peer_ports):
                download_from_peers(server_socket, peer_ports, file_name)
        elif(command == "chunk selection"): # uses chunk selection by determining rarity
            file_name = input("File name: ")
            chunk_selection(server_socket, file_name)
        else:
            print("not a valid command: ",commands)


#Allow other peers to connect to this user, 
# use a thread
def start_connection(st, Selfport):
    
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

                #sends data to the server and will notify the user of which file chunk was requested 
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

            
    #registers the file with the server upon downloading
    register(server_socket, file_name)
    
    file_integrity = True
    #checks the integrity of file
    for i in range(len(chunks)):
        right_integrity = download_and_verify_chunk(server_socket, file_name, chunks[i], i)
        if(right_integrity == False):
            chunks[i] = None

    #combiners the data
    with open("newfile.txt", 'wb') as file:
        for chunk in chunks:
            file.write(chunk)

# Outputs a list of files, their sizes, and which peer owns them
def get_list_of_files(server_socket):
    #request to server
    server_socket.sendall("file list".encode('utf-8')) 

    #reply from server
    data = server_socket.recv(1024)
    file_list = data.decode('utf-8').split(',')

    print(f"{file_list}")


def get_file_location(server_socket, file_name):

     #request to server 
    server_socket.sendall("file location".encode('utf-8'))
    server_socket.sendall(file_name.encode('utf-8'))

    #reply from server
    file_locations = server_socket.recv(1024).decode('utf-8').split(',')

    # ensures a valid file
    if (file_locations[0] == "NULL"):
        print("Not a valid file")
        return

    # List of port numbers
    int_list = []
    for num in file_locations:
        int_list.append(int(num))

    print(f"{len(int_list)} endpoints") # outputs the number of endpoints
 
    for port in int_list:
        print(f'127.0.0.1:{port}') # outputs each peers IP:Port (all are local host) 
    return int_list
    

#registers a file with the server
'''
when a file is registered with the server, the server should give the user a port number
client gives the server:
'''
def register(server_socket, file_name):
    # ensures the file exists in the working directory
    if os.path.exists(file_name):
        file_size = os.path.getsize(file_name)

        #sends commands command and file name to server
        server_socket.sendall("register".encode('utf-8'))
        server_socket.sendall(file_name.encode('utf-8'))

        # confirm message
        confirmation = server_socket.recv(1024)
        if(not confirmation):
            return
        
        server_socket.sendall(file_size.to_bytes(8, byteorder='big'))
        server_socket.sendall(Selfport.to_bytes(8, byteorder='big'))

        files[file_name] = split_file_into_chunks(file_name, DEFAULT_CHUNK_SIZE)
        #print("files: ", files)

        send_hash(server_socket, file_name)
        #start_connection(Selfport) #once registered, user now can be connect from other clients

        print(f"File {file_name} registered with the server!")
    else:
        print("File doesn't exist")


# user tells the server that it received a new chunk and that other users can download it from th 
def chunk_register(server_socket, file_name):
    #ensures the file is in the directory
    if os.path.exists(file_name):
        # splits the file into chunks and asks the user which 
        chunks = split_file_into_chunks(file_name, DEFAULT_CHUNK_SIZE)
        print("num of chunks: ", len(chunks))
        file_size = os.path.getsize(file_name)

        #input from user for chunnk and assigned port
        chunk_num = int(input("which chunk to send (len-1): "))
        
        server_socket.sendall("chunk register".encode('utf-8'))
        server_socket.sendall(file_name.encode('utf-8'))

        confirmation = server_socket.recv(1024)
        if(not confirmation):
            return
    
        server_socket.sendall(chunk_num.to_bytes(8, byteorder='big'))
        server_socket.sendall(file_size.to_bytes(8, byteorder='big'))
        server_socket.sendall(Selfport.to_bytes(8, byteorder='big'))

        #append the chunk to a list of chunks for the file, o.w. create first chunk
        files[file_name] = split_file_into_chunks(file_name, DEFAULT_CHUNK_SIZE)
        
        

        print(f"File {file_name} registered with the server!")
    else:
        print("File doesn't exist")

# helper func to verify the hash of the downloaded chunk
def verify_chunk(chunk_data, expected_hash):
    received_hash = hashlib.sha256(chunk_data).hexdigest()
    return received_hash == expected_hash


# Downloads a chunk and uses the helper to verify
def download_and_verify_chunk(server_socket, file_name, chunk, chunk_num):
    #chunk = server_socket.recv(DEFAULT_CHUNK_SIZE)  # Receive chunk data
    server_socket.sendall("verify chunk".encode('utf-8'))
    confirmation = server_socket.recv(1024)
    if(not confirmation):
        return
    server_socket.sendall(file_name.encode('utf-8'))
    server_socket.sendall(chunk_num.to_bytes(8, byteorder='big'))
    chunk_hash = server_socket.recv(64).decode('utf-8')  # Receive chunk hash (SHA-256 hex is 64 chars)
    # Verify the chunk data

    if verify_chunk(chunk, chunk_hash):
        #outuput the match and store file
        print(f"Chunk {chunk_num} matches hash")
        with open(file_name, 'ab') as f:
            f.write(chunk)
    else: #discard if hashes differ
        print(f"Chunk {chunk_num} wrong chunk")


def send_hash(server_socket, file_name):
    server_socket.sendall("store hash".encode('utf-8'))

    chunks = split_file_into_chunks(file_name, DEFAULT_CHUNK_SIZE)
    chunk_hashes = []
    for chunk_num in range(len(chunks)):
        chunk_hash = hashlib.sha256(chunks[chunk_num]).hexdigest()  # Compute the hash
        chunk_hashes.append(chunk_hash)
        print(f"Chunk {chunk_num} hash: {chunk_hash}")
    data_list = ','.join(chunk_hashes)
    server_socket.sendall(file_name.encode('utf-8'))
    server_socket.sendall(data_list.encode('utf-8'))

    print("sent hash to server")


# takes a file and splits into multiple chunks based on DEFAULT_CHUNK_SIZE. @return a list of chunks
def split_file_into_chunks(file_path, chunk_size):
    chunks = []
    with open(file_path, 'rb') as file:
        while True:
            #read in a chunk of data until no more data is left
            chunk = file.read(chunk_size)
            if not chunk:  
                break
            chunks.append(chunk)
    return chunks

#Send a message to the server
def send(server_socket, message):
    server_socket.sendall(message.encode('utf-8'))  # Send the message encoded

#Confirmation message
def send_confirmation(client_socket):
    client_socket.sendall("confirm".encode('utf-8'))


#Receive message from server
def recv(server_socket):
    data = server_socket.recv(1024)
    print(f"Received from server: {data.decode('utf-8')}")

#handles closing the client
def close_client(server_socket):
    server_socket.close()
    print("closing")
    
#Uses rarity to determine where a chunk should be downloaded from
def chunk_selection(server_socket, file_name):
    server_socket.sendall("chunk selection".encode('utf-8'))  
    server_socket.sendall(file_name.encode('utf-8'))  

    availability_data = server_socket.recv(1024).decode('utf-8')
    if availability_data == "NULL":
        print("No such file exists on the server.")
        return

    # parse the availability data
    availability = {}
    lines = availability_data.split('\n')
    for line in lines:
        if line:  # Ensure line is not empty
            parts = line.split(':')
            if len(parts) >= 2:  # Check that parts has at least 2 elements
                try:
                    # references to get values of chunks
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

    # Selects the chunk with fewer occasions
    rarest_chunk = min(availability, key=availability.get)
    rarest_chunk_count = availability[rarest_chunk]
    print(f"The rarest chunk is {rarest_chunk} with {rarest_chunk_count} peers holding it.")

    # downloads the specific chunk
    download_chunk(server_socket, file_name, rarest_chunk)

def download_chunk(server_socket, file_name, chunk_num):
    # Send a request to the server for the specified chunk
    server_socket.sendall("request chunk".encode('utf-8'))  
    server_socket.sendall(file_name.encode('utf-8'))  
    server_socket.sendall(chunk_num.to_bytes(8, byteorder='big')) 

    #Get data from server
    chunk_size = int.from_bytes(server_socket.recv(8), byteorder='big')  # Receive chunk size
    chunk_data = server_socket.recv(chunk_size)  # Receive the actual chunk data

    # If the chunk is found
    if chunk_data:
        print(f"Received chunk {chunk_num} of file {file_name}.")
        # Save the chunk to a file
        with open(f"chunk_{file_name}_{chunk_num}.bin", 'wb') as f:
            f.write(chunk_data)
        print(f"Chunk {chunk_num} saved as chunk {file_name} {chunk_num}.bin")
    else:
        print(f"Failed to receive chunk {chunk_num} of file {file_name}.")

if __name__ == '__main__':
    Selfport = int(input("User port (0 - 65535): " ))
    thread1 = threading.Thread(target=connect_to_server)
    thread2 = threading.Thread(target=start_connection, args = ("localhost", Selfport))
    thread2.start()
    thread1.start()
    


    