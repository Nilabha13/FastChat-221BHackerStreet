import socket, select, sys
from constants import *
from utilities import *

# LOAD_BALANCER_PORT = 5000

def display_pending_messages(messages):
	print(f"You have {len(messages)} pending messages!")
	for msg in messages:
		print(msg)

username = input("Enter a username: ")
initial = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
initial.connect(('localhost', LOAD_BALANCER_PORT))
lb_response = from_recv(initial.recv(1024))
token = lb_response["token"]
server_port = lb_response["server port"]
server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_connection.connect(('localhost', server_port))
print(username)
server_connection.send(to_send({"command": "first connection", "authentication token": token, "username": username}))
list_of_messages = []
while True:
	rlist, wlist, elist = select.select([server_connection, sys.stdin], [], [])
	for s in rlist:
		if s == server_connection:
			# data = s.recv(4096)
			# if not data:
			#     print('\33[31m\33[1m \rDISCONNECTED!!\n \33[0m')
			#     sys.exit()
			# elif "Welcome" in data.decode():
			#     print(data.decode())
			# else:
			#     list_of_messages.append(data.decode())
			data = s.recv(4096)
			if not data:
				print('\33[31m\33[1m \rDISCONNECTED!!\n \33[0m')
				sys.exit()
			response = from_recv(data)
			command = response["command"]
			if command == "new user":
				print("Welcome to FastChat - the application which lets you chat faster than the speed of light!")
				print("You are a new user!")
				password = input("Please enter a password: ")
				server_connection.send(to_send({"command": "new password", "password": password}))
			elif command == "existing user":
				print("Welcome to FastChat - the application which lets you chat faster than the speed of light!")
				print("You are an existing user!")
				password = input("Please enter your password: ")
				server_connection.send(to_send({"command": "password authenticate", "password": password}))
			elif command == "re-enter":
				print("The password you entered is incorrect!")
				password = input("Please enter your password: ")
				server_connection.send(to_send({"command": "password authenticate", "password": password}))
			elif command == "register for keyServer":
				pass
				# pass
			elif command == "pending messages":
				print("Password Authenticated!")
				messages = response["messages"]
				display_pending_messages(messages)
				print("""
				Enter command:
				1) READ
				2) SEND
				""")
		else:
			# message = sys.stdin.readline()
			# if(message.split("-", 1)[0].strip() == "read"):
			#     while len(list_of_messages) > 0:
			#         print(list_of_messages.pop(0))
			#     sys.stdout.flush()
			# else:
			#     server_connection.send(message.encode())
			#     sys.stdout.flush()
			command  = sys.stdin.readline()
			if command == "READ" or command == '1':
				# from_user = input("Enter username whose messages you want to read: ")
				while len(list_of_messages) > 0:
					print(list_of_messages.pop(0))
			elif command == "SEND" or command == '2':
				message = input("Enter message: ")
				to_username = input("Enter to username: ")
				server_connection.send(to_send({"command": "user-user message","encrypted message": message, "receiver username": to_username, "sender username": username}))
			else:
				print("Invalid command!")


