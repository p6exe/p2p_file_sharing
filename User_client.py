import socket
import threading
import os

HOST = '127.0.0.1'  #The server's hostname or IP address
PORT = 58008        #The port used by the server

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
        elif(command == "register"):
            file_location = input("File Location: ")
            send_file(server_socket, 'Testfile.txt')
        else:
            print("type help for commands: ",commands)
        
#registers a file with the server
def send_file(server_socket, file_path):

    server_socket.sendall("register".encode('utf-8'))

    with open(file_path, 'rb') as file:
        #Send the size of the file
        file_size = os.path.getsize(file_path)
        server_socket.sendall(file_size.to_bytes(8, byteorder='big'))

        #Read the file in chunks and send each chunk
        while True:
            chunk = file.read(1024)
            if not chunk:  # If no more data, break out of the loop
                break
            server_socket.sendall(chunk)

    print(f"File {file_path} sent successfully!")

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
    #send(server_socket, "Message received!")  # Send acknowledgment

#handles closing the client
def close_client(server_socket):
    server_socket.close()
    print("closing")
    

if __name__ == '__main__':
    connect_to_server()