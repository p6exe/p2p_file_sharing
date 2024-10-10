import socket
import select
import threading
import os

HOST = '127.0.0.1'  #The server's hostname or IP address
PORT = 58008        #The port used by the server

file_name = [] #current stores the file name since the file will be stored locally

#established when the user enters the value into the command:
SELFHOST = HOST         #client ip address
SELFPORT = PORT + 1     #client port

files = {}   #{file_name: [chunks]}, file is added when calling register
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
        elif(command == "download"):
            file_name = input("File name: ")
            peer_ports = get_file_location(file_name)
            if(peer_ports):
                download_from_peers(server_socket, peer_ports, file_name)
        else:
            print("type help for commands: ",commands)


#Allow other peers to connect to this user, 
# use a thread
def start_connection():
    
    send_buffer = {}    # Buffers that stores the sockets that need a reply after they request
    sockets_list = []   # List of all sockets (including server socket)

    self_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket
    self_socket.bind((HOST, SELFPORT))
    self_socket.listen(4)     #Listen for incoming connections
    sockets_list.append(self_socket)
    self_socket.setblocking(False)
    print(f"client starting on {HOST}:{SELFPORT}")

    chunk_num = -1

    #send the specified chunk
    while True:
        readable, writable, exceptional = select.select(sockets_list, sockets_list, sockets_list)
        for current_socket in readable:
            if current_socket == self_socket: #establish new connections

                peer_socket, peer_address = peer_socket.accept()
                print(f"Connected by {peer_address}")
                
                #Set the client socket to non-blocking and add to monitoring list
                peer_socket.setblocking(True)
                sockets_list.append(peer_socket)
            else:   #recvs the chunk and filename the user wants to download
                chunk_num = int.from_bytes(peer_socket.recv(8), byteorder='big')
                file_name = peer_socket.recv(1024).decode('utf-8')
                send_buffer.append(current_socket)
                print("sending file: ", file_name, " chunk: ", chunk_num)

        #send teh chunk to the peer
        for current_socket in writable:
            if((current_socket in send_buffer) and chunk_num != -1):
                current_socket.sendall(files[file_name][chunk_num])


#download from peers
def download_from_peers(server_socket, peer_ports, file_name):
    server_socket.sendall("download".encode('utf-8'))

    peer_sockets_list = []
    peer_ports = server_socket.recv(1024).decode('utf-8').split(',')
    chunk_size = server_socket.recv(1024)
    num_of_chunks = server_socket.recv(1024)
    chunks = [None]*num_of_chunks #stores all the chunks downloaded

    #should i use threading?
    #connect to the peers
    for peer in peer_ports:
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect(peer)
        peer_sockets_list.append(peer_socket)
    
    # Use select to wait for data to be available
    while (peer_sockets_list):
        readable, writable, exceptional = select.select(peer_sockets_list, peer_sockets_list, [])

        #request for a chunk
        for peer_socket in writable:
            chunk_num = peer_sockets_list.index(peer_socket)
            peer_socket.sendall(chunk_num.to_bytes(8, byteorder='big'))
            peer_socket.sendall(file_name.encode('utf-8'))

        #gets the download
        for peer_socket in readable:
            chunk_num = int.from_bytes(peer_socket.recv(8), byteorder='big')
            chunks[chunk_num] = peer_socket.recv(chunk_size)
            peer_sockets_list.remove(peer_socket)

            show_download_progress(chunks)

            '''if data:
                print(f"Received data: {data.decode()}")
                peer_sockets_list.remove(peer_socket)
                show_download_progress(chunks)
            else:
                # Peer has closed the connection
                print("Peer closed the connection.")
                peer_sockets_list.remove(peer_socket)
                peer_socket.close()'''

    #disconnect from peers
    for peer in peer_ports:
        pass

def show_download_progress(chunks):
    progress = ""
    for chunk in chunks:
        if():
            pass


def get_list_of_files(server_socket):
    #request to server
    server_socket.sendall("file list".encode('utf-8')) 

    #reply from server
    data = server_socket.recv(1024)
    file_list = data.decode('utf-8').split(',')

    print(f"List of files: {file_list}")



def get_file_location(server_socket, file_name):
    #request to server 
    server_socket.sendall("file location".encode('utf-8'))
    server_socket.sendall(file_name.encode('utf-8'))

    #reply from server
    data = server_socket.recv(1024)
    file_locations = data.decode('utf-8').split(',')
    if (file_locations[0] != "NULL"):
        print("File locations: ", file_locations)
        return file_locations
    else:
        print("Not a valid file")



#registers a file with the server
'''
when a file is registered with the server, the server should give the user a port number
client gives the server:
'''
def register(server_socket, file_name):
    if os.path.exists(file_name):
        file_size = os.path.getsize(file_name)

        server_socket.sendall("register".encode('utf-8'))
        server_socket.sendall(file_name.encode('utf-8'))

        confirmation = server_socket.recv(1024)
        if(not confirmation):
            return
        
        server_socket.sendall(file_size.to_bytes(8, byteorder='big'))
        server_socket.sendall(SELFPORT.to_bytes(8, byteorder='big'))

        files[file_name] = split_file_into_chunks(file_name, DEFAULT_CHUNK_SIZE)
        #print("files: ", files)

        start_connection() #once registered, user now can be connect from other clients

        print(f"File {file_name} registered with the server!")
    else:
        print("File doesn't exist")


'''
#send file to peer
def send_file(peer_socket, file_name):

    peer_socket.sendall("register".encode('utf-8'))

    with open(file_name, 'rb') as file:

        #Send the size of the file
        file_size = os.path.getsize(file_name)
        peer_socket.sendall(file_size.to_bytes(8, byteorder='big'))

        #Read the file in chunks and send each chunk
        while True:
            chunk = file.read(1024)
            if not chunk:  # If no more data, break out of the loop
                break
            peer_socket.sendall(chunk)

    print(f"File {file_name} sent successfully!")
'''


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
    

if __name__ == '__main__':
    connect_to_server()