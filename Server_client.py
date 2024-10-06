import socket
import select

'''
tasks:
establish multiple connects
break up a file
send file
communication between server and client
integrity checks
'''

HOST = '127.0.0.1'  # Localhost
PORT = 58008        # Port 

sockets_list = []
#Dictionary to store multiple addresses
clients = {}

#Start the server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket
    server_socket.bind((HOST, PORT))  #Bind the socket to the host and port
    server_socket.listen(4)     #Listen for incoming connections
    server_socket.setblocking(False)
    sockets_list.append
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
                client_socket.setblocking(False)
                clients[client_socket] = client_address
                sockets_list.append(client_socket)
                
            
            else: #Receive data

                data = current_socket.recv(1024)
                if data:
                    print(f"Received from {clients[current_socket]}: {data.decode()}")
                    
                else: #Handle client disconnection
                    
                    print(f"Client {clients[current_socket]} disconnected")
                    sockets_list.remove(current_socket)
                    del clients[current_socket]
                    current_socket.close()

        #Handle Writable sockets
        for current_socket in writable:
            send(current_socket, "hello")

#Create a socket
def create_socket(server_socket):
    client_socket = 0
    client_socket, client_address = server_socket.accept()  # Accept a new connection
    clients[client_address] = client_socket  # Store client in the dictionary
    print(f"Connected by {client_address}")

    send(client_socket, "hello")

#listens for commands from clients
def listen_to_socket():
    pass

#Send a message to a specific client
def send(client_socket, message):
    try:
        client_socket.sendall(message.encode('utf-8'))  # Send the message encoded as bytes
    except Exception as e:
        print(f"Error sending message: {e}")

#Receive messages from the client
def recv(client_socket, addr):
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"Received from {addr}: {data.decode('utf-8')}")
            send(client_socket, "Message received!")  # Send acknowledgment
    except ConnectionResetError:
        print(f"Client {addr} disconnected")
    finally:
        client_socket.close()
        del clients[addr]

#Close the server and all client connections
def close_server(server_socket):
    print("Closing server and all client connections.")
    for addr, client_socket in clients.items():
        client_socket.close()  #Close each client socket
    server_socket.close()  #Close the server socket
    print("Server closed.")

def create_distributed_file():
    pass

def distribute_file():
    pass

if __name__ == '__main__':
    start_server()