import socket
import select

'''
commands the server takes:
close

tasks:
establish multiple connects
communication between server and client
communication between clients
break up a file
send file
integrity checks
'''

HOST = '127.0.0.1'  # Localhost
PORT = 58008        # Port 

sockets_list = []
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
                sockets_list.append(client_socket)
                
            else: #Receive data
                recv(current_socket)
                
        #Handle Writable sockets
        for current_socket in writable:
            send(current_socket, "hello")

#Create a socket
def create_socket(server_socket):
    client_socket = 0
    client_socket, client_address = server_socket.accept()  # Accept a new connection
    client_addresses[client_address] = client_socket  # Store client in the dictionary
    print(f"Connected by {client_address}")

    send(client_socket, "hello")


#Send a message to a specific client
def send(client_socket, message):
    try:
        print(client_socket)
        client_socket.sendall(message.encode('utf-8'))
    except ConnectionError as e:
        close_socket(client_socket)

#Receive commands from the client
def recv(client_socket):
    try:
        data = client_socket.recv(1024)
        print(f"Received from {client_addresses[client_socket]}: {data.decode('utf-8')}")

        #closes
        if(data.decode('utf-8') == "close"):
            close_socket(client_socket)
    except ConnectionError as e:
        #Handle client disconnection
        close_socket(client_socket)
        

#Close the server and all client connections
def close_server(server_socket):
    print("Closing server and all client connections.")
    for addr, client_socket in client_addresses.items():
        client_socket.close()  #Close each client socket
    server_socket.close()  #Close the server socket
    print("Server closed.")

#handles closing sockets
def close_socket(client_socket):
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