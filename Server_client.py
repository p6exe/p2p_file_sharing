import socket
import threading

#Server configuration
HOST = '127.0.0.1'  # Localhost
PORT = 80085        # Port to listen on (non-privileged ports are > 1023)

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


# Start the server when this script is run
if __name__ == '__main__':
    connect_socket()