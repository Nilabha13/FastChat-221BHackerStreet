import socket, select
import psycopg2
import sys
from utilities import *

def send_pending_messages(sock):
	# a user is authenticated, send him stored messages from the database
	sock.send(to_send({'command':'pending messages', 'messages':[]}))
	pass

def authenticate(sock, password):
	global validated
	global socket_name
	global name_socket
	global connected_list
	global number

	username = socket_name[sock]
	if(validated[sock] in [0,1]):
		conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="Ameya563")
		cur = conn.cursor()
		cur.execute(f"SELECT password_hash FROM USERS WHERE username LIKE '{username}'")
		pass_real = cur.fetchall()[0][0]
		print("Real password of this user: ", pass_real)
		print("password entered by user: ", password)
		if(pass_real == password):
			validated[sock] = 3
			sock.send(to_send({'command' : 'password accepted'}))
			send_pending_messages(sock)
			#send_to_all(sock, f"\33[32m\33[1m\r Existing user {username} joined the conversation \n\33[0m")
		else:
			sock.send(to_send({'command' : 're-enter'}))
			validated[sock] += 1
		cur.close()
		conn.close()
		return
	
	elif(validated[sock] == 2):
		#entering the password the final 3rd time
		print("user: ", username, " is attempting final login ", password)
		conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="Ameya563")
		cur = conn.cursor()
		cur.execute(f"SELECT password_hash FROM USERS WHERE username LIKE '{username}'")
		pass_real = cur.fetchall()[0][0]
		print("Real password of this user: ", pass_real)
		print("password entered by user: ", password)
		if(pass_real == password):
			validated[sock] = 3
			sock.send(to_send({'command' : 'password accepted'}))
			send_pending_messages(sock)
			#send_to_all(sock, f"\33[32m\33[1m\r Existing user {username} joined the conversation \n\33[0m")
			cur.execute(f"UPDATE fastchatdb SET current_server_number = {number} WHERE username = '{username}'")
		else:
			sock.send(to_send({'command' : 'error', 'type' : 'wrong password error'}))
			del socket_name[sock]
			del name_socket[username]
			connected_list.remove(sock)
			sock.close()
		cur.close()
		conn.close()
		return

def add_new_user(sock, password):
	global validated
	global socket_name
	global name_socket
	global connected_list
	global number
	username = socket_name[sock]
	print("user: ", username, " has entered password: ", password)
	conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="Ameya563")
	cur = conn.cursor() 
	cur.execute("SELECT COUNT(*) FROM USERS")
	count = cur.fetchall()[0][0]
	print("number of users here yet: ", count)

	cur.execute(f'''INSERT INTO USERS(user_id, username, password_hash, current_server_number) VALUES 
	({count + 1}, '{username}', '{password}', {number})
	''')
	print("data insertions done!")
	conn.commit()
	cur.close()
	conn.close()
	sock.send(to_send({'command' : 'register for keyServer'}))
	#send_to_all(sock, f"\33[32m\33[1m\r New user {record[(i,p)]} joined the conversation \n\33[0m")
	validated[sock] = 3	

LOAD_BALANCER_PORT = 5000
NUM_SERVERS = 5
self_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
self_port = int(sys.argv[1])
ip = 'localhost'
port = int(sys.argv[1])
number = port - 5000
#add self_server_socket to connected_list
self_server_socket.bind((ip, port))
self_server_socket.listen(10)

#a dictionary with client names
socket_name = {}
name_socket = {}
#a dictionary with validated status of connections
validated = {}
tokens = ["default"]
connected_list = []
connected_list.append(self_server_socket)
#connect to load balancer with a new socket ON THE SAME PORT
lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lb_socket.bind((ip, 5000 + 100 * number))
lb_socket.connect(('localhost', LOAD_BALANCER_PORT))
next_server_ports = []
for i in range(number + 1, NUM_SERVERS + 1):
	next_server_ports.append(5000 + i * 100 + number)

other_servers_sockets = []
#connect to prev running servers with NEW SOCKETS on the SAME PORT
for i in range(5001, self_port):
	curr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	curr.bind((ip, i + number * 100))
	curr.connect(('localhost', i))
	print(curr.recv(1024).decode())
	other_servers_sockets.append(curr)

other_servers_sockets.append(lb_socket)

while True:
	rlist, wlist, elist = select.select(connected_list + other_servers_sockets, [], [])
	for sock in rlist:
		if sock == self_server_socket:
			new_conn_socket, addr = self_server_socket.accept()
			#the new connection is another server
			if addr[1] in next_server_ports:
				other_servers_sockets.append(new_conn_socket)
				new_conn_socket.send(("Hey from " + str(port)).encode())
			#the new connection is a client
			else:
				#handle cases
				data = new_conn_socket.recv(1024)
				dict = from_recv(data)
				try:
					if dict['command'] == 'first connection' and dict['authentication token'] in tokens:
						tokens.remove(dict['authentication token'])
						connected_list.append(new_conn_socket)
						client_name = dict['username']
						socket_name[new_conn_socket] = client_name
						name_socket[client_name] = new_conn_socket
						#check if the user name received is in the database
						existing_user = False
						conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="Ameya563")
						cur = conn.cursor()
						cur.execute(f"SELECT * FROM USERS WHERE username = '{client_name}'")
						for i in cur.fetchall():
							if(i[1] == client_name):
								existing_user = True
						cur.close()
						conn.close()
						if(existing_user):
							validated[new_conn_socket] = 0
							print("Client (%s, %s) attempting login" % addr," [",socket_name[new_conn_socket],"]")
							new_conn_socket.send(to_send({'command' : 'existing user'}))
						else:
							validated[new_conn_socket] = -1
							print("New client (%s, %s) registering" % addr," [",socket_name[new_conn_socket],"]")
							new_conn_socket.send(to_send({'command' : 'new user'}))
				except:
					new_conn_socket.send(to_send({'command' : 'error', 'type' : 'wrong authentication token'}))
		elif sock == lb_socket:
			#Load balancer sending a token to validate
			token = sock.recv(4096)
			dict = from_recv(token)
			if dict['command'] == 'authentication token':
				tokens.append(dict['token'])

		elif sock in other_servers_sockets:
			#other servers send "user2 - user1 : message", where user2 in connected list
			data = sock.recv(4096)
			dict = from_recv(data)
			try:
				if dict['command'] == 'user-user message':
					user2 = dict['receiver username']
					if user2 in name_socket.keys() and validated[name_socket[user2]] == 3:
						user_sock = name_socket[user2]
						user_sock.send(to_send(dict))
					else:
						#store the messages in the database
						pass
			except:
				pass
		else:
			#a connected user sending a message
			#case 1: a user trying to get autheticated
			try:
				dict = from_recv(sock.recv(4096))
				if dict['command'] == 'new user':
					password =dict['password']
					add_new_user(sock, password)
				elif dict['command'] == 'password authentication':
					password = dict['password']
					authenticate(sock, password)
				elif dict['command'] == 'user-user message':
					#user2 - message
					sender = socket_name[sock]
					if sender == dict['sender username']:
						user2 = dict['receiver username']
						message = dict['encrypted message']
						print(message)
						conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="Ameya563")
						cur = conn.cursor()
						cur.execute(f"SELECT current_server_number FROM USERS WHERE username = '{user2}'")
						db_data = cur.fetchall()
						valid = False
						if len(db_data) == 0:
							sock.send(to_send({'command' : 'error', 'type' : 'user not found'}))
						else:
							valid = True
							receiver_server = db_data[0][0]
						cur.close()
						conn.close()
						if valid:
							if receiver_server == number:
								if user2 in name_socket.keys() and validated[name_socket[user2]] == 3:
									user2_sock = name_socket[user2]
									user2_sock.send(to_send(dict))
								else:
									#store in the database
									pass
							else:
								if receiver_server < number:
									receiver_port = 5000 + receiver_server
								else:
									receiver_port = 5000 + 100 * receiver_server + number
								for s in other_servers_sockets:
									ip, r_port = s.getpeername()
									#print(r_port)
									if r_port == receiver_port:
										s.send(to_send(dict))
			except:
				sender = socket_name[sock]
				sock.close()
				connected_list.remove(sock)
				del socket_name[sock]
				del name_socket[sender]

				


					

			
				






