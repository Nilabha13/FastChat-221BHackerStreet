import socket, select, sys
from constants import *
from utilities import *

# LOAD_BALANCER_PORT = 5000

username = input("Enter a username: ")
initial = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
initial.connect(('localhost', LOAD_BALANCER_PORT))
token = initial.recv(1024).decode()
arr = token.split("-", 1)
auth = arr[0].strip()
server_port = int(arr[1].strip())
server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_connection.connect(('localhost', server_port))
print(username)
server_connection.send((f"{auth} - {username}").encode())
while True:
    rlist, wlist, elist = select.select([server_connection, sys.stdin], [], [])
    for s in rlist:
        if s == server_connection:
            data = s.recv(4096)
            if not data :
                print('\33[31m\33[1m \rDISCONNECTED!!\n \33[0m')
                sys.exit()
            else :
                print("hey")
                sys.stdout.write(data.decode())
        else:
            message = sys.stdin.readline()
            server_connection.send(message.encode())

