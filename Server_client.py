import socket

# Server configuration
HOST = '127.0.0.1'  # Localhost
PORT = 80085        # Port to listen on (non-privileged ports are > 1023)

# Dictionary to store multiple addresses
clients = {}

# Create and start the server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket
    server_socket.bind((HOST, PORT))  # Bind the socket to the host and port
    server_socket.listen(5)     # Listen for incoming connections 

    print(f"Server started on {HOST}:{PORT}")
    
    #connects to multiple clients
    while True:
        client_socket, addr = server_socket.accept()  # Accept a new connection
        clients[addr] = client_socket  # Store client in the dictionary
        print(f"Connected by {addr}")
        recv(client_socket, addr)

def create_distributed_file():
    pass

# Send a message to a specific client
def send(client_socket, message):
    try:
        client_socket.sendall(message.encode('utf-8'))  # Send the message encoded as bytes
    except Exception as e:
        print(f"Error sending message: {e}")

# Receive messages from the client
def recv(client_socket, addr):
    try:
        while True:
            data = client_socket.recv(1024)  # Receive data from the client
            if not data:
                break
            print(f"Received from {addr}: {data.decode('utf-8')}")
            send(client_socket, "Message received!")  # Send acknowledgment
    except ConnectionResetError:
        print(f"Client {addr} disconnected")
    finally:
        client_socket.close()
        del clients[addr]

# Close the server and all client connections
def close_server(server_socket):
    print("Closing server and all client connections.")
    for addr, client_socket in clients.items():
        client_socket.close()  # Close each client socket
    server_socket.close()  # Close the server socket
    print("Server closed.")


def distribute_file():
    pass
# Start the server when this script is run
if __name__ == '__main__':
    start_server()