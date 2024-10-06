import socket
import threading

HOST = '127.0.0.1'  #The server's hostname or IP address
PORT = 58008        #The port used by the server

#Connects to the server socket
def connect_to_server():
    # Create a socket (TCP/IP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((HOST, PORT))  # Connect to the server

    print(f"client connecting to server {HOST}:{PORT}")

    # Receive a response from the server
    recv(server_socket)
    close_client(server_socket)

#Send a message to the server
def send(server_socket, message):
    server_socket.sendall(message.encode('utf-8'))  # Send the message encoded

#Receive message from server
def recv(server_socket):
    data = server_socket.recv(1024)
    print(f"Received from server: {data.decode('utf-8')}")
    #send(server_socket, "Message received!")  # Send acknowledgment

def close_client(server_socket):
    server_socket.close()

if __name__ == '__main__':
    connect_to_server()