import socket
import select
import os

HOST = '127.0.0.1'  #The server's hostname or IP address
PORT = 58008        #The port used by the server

file_name = [] #current stores the file name since the file will be stored locally

#established when the user enters the value into the command:
SELFHOST = HOST    #client ip address
SELFPORT = PORT + 1    #client port


send_buffer = {}    # Buffers that stores the sockets that need a reply after they request
sockets_list = []   # List of all sockets (including server socket)


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
                download_from_peers(server_socket, peer_ports)
            else:
                print("This is not a file name")
        else:
            print("type help for commands: ",commands)


#Allow other peers to connect to this user
def start_connection():
    self_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket
    self_socket.bind((HOST, SELFPORT))
    self_socket.listen(4)     #Listen for incoming connections
    sockets_list.append(self_socket)
    self_socket.setblocking(False)

    
    #send the specified chunk
    '''while True:
        readable, writable, exceptional = select.select(sockets_list, sockets_list, sockets_list)
        for current_socket in writable:
            if(current_socket in send_buffer):
                send(current_socket, "hello")'''


#download from peers
def download_from_peers(server_socket, peer_ports):

    sockets_list = []
    json_data = server_socket.recv(1024).decode('utf-8')
    peer_ports = json.loads(json_data)
    
    for peer in peer_ports:
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.setblocking(False)  # Set to non-blocking
        try:
            peer_socket.connect(peer)
        except BlockingIOError:
            # Non-blocking connect; do nothing
            pass
        sockets_list.append(peer_socket)
    
    # Use select to wait for data to be available
    while (sockets_list):
        readable, _, _ = select.select(sockets_list, [], [])

        for peer_socket in readable:
            try:
                data = peer_socket.recv(1024)  # Buffer size
                if data:
                    print(f"Received data: {data.decode()}")
                else:
                    # Peer has closed the connection
                    print("Peer closed the connection.")
                    sockets_list.remove(peer_socket)
                    peer_socket.close()
            except Exception as e:
                print(f"Error receiving data: {e}")
                sockets_list.remove(peer_socket)
                peer_socket.close()



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

        start_connection() #once registered, user now can be connect from other clients

        print(f"File {file_name} registered with the server!")
    else:
        print("File doesn't exist")


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