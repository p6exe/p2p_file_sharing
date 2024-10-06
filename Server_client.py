import socket
import threading

#Server configuration
HOST = '127.0.0.1'  # Localhost
PORT = 58008        # Port 

#Dictionary to store multiple addresses
clients = {}

#Create a socket
def connect_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket
    server_socket.bind((HOST, PORT))  # Bind the socket to the host and port
    server_socket.listen(5)     # Listen for incoming connections 

    print(f"Server started on {HOST}:{PORT}")
    
    
    client_socket, addr = server_socket.accept()  # Accept a new connection
    clients[addr] = client_socket  # Store client in the dictionary
    print(f"Connected by {addr}")
    send(client_socket, "hello")

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
        client_socket.close()  # Close each client socket
    server_socket.close()  # Close the server socket
    print("Server closed.")

def create_distributed_file():
    pass


def distribute_file():
    pass

if __name__ == '__main__':
    connect_socket()