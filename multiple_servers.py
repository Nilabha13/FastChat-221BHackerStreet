import socket, select
import psycopg2
import sys
from utilities import *
from constants import *
import crypto
import re
import os

logfd = open(f"logs/servers_logs/server{sys.argv[1]}.log", 'w')
def log(msg):
    log_to_file(msg, logfd)


prev_users = []
r = re.compile(f"(servers_)(.*)(_pub_key.pem)")
for i in os.listdir("mykeys"):
	match = re.search(r, i)
	if match != None:
		prev_users.append(match.group(2))

def encryptData(data, to_username, is_image=False, type = 'fastchatter'):
	global prev_users
	if not is_image:
		data = data.encode()
	if to_username not in prev_users:
		ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ks.connect(('localhost', KEYSERVER_PORT))
		log("Connecting to the key server")
		ks.send(to_send({"command": "RETRIEVE", "username": to_username, 'type':type}))
		ks_response = from_recv(ks.recv(4096))
		if ks_response["command"] == "PUBKEY":
			
			to_user_pubkey = crypto.str_to_key(ks_response["pubkey"])
			signature = b64decode(ks_response["signature"].encode())
			ks_pubkey = crypto.import_key("KEYSERVER_PUBKEY.pem")

			if not crypto.verify_signature(ks_pubkey, ks_response['pubkey'].encode(), signature):
				
				# fp(signature)
				# fp(crypto.decryptRSA(ks_pubkey, signature))
				# fp(crypto.sha256(ks_response['pubkey'].encode()).digest())
				log("Malicious tampering with keyserver!")
			
			crypto.export_key(to_user_pubkey, f"mykeys/servers_{to_username}_pub_key.pem")
			prev_users.append(to_username)
			log(f"Public key of {to_username} successfully retrieved")
			return b64encode(crypto.encryptRSA(to_user_pubkey, data)).decode()
		else:
			log("Keyserver error")
	else:
		
		to_user_pubkey = crypto.import_key(f"mykeys/servers_{to_username}_pub_key.pem")
		return b64encode(crypto.encryptRSA(to_user_pubkey, data)).decode()

def send_pending_messages(sock):
	global socket_name
	# a user is authenticated, send him stored messages from the database
	username = socket_name[sock]
	pending = []
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor()
	log("Fetching pending messages from the databases")
	cur.execute(f"SELECT * FROM INDIVIDUAL_MESSAGES WHERE to_user_name = '{username}'")
	messages = cur.fetchall()
	cur.execute(f"DELETE FROM INDIVIDUAL_MESSAGES WHERE to_user_name = '{username}'")
	conn.commit()
	cur.close()
	conn.close()
	while len(messages) > 0:
		message = messages.pop()
		dict = {}
		dict['command'] = 'user-user message'
		dict['encrypted message'] = message[2]
		dict['sender username'] = message[0]
		dict['receiver username'] = message[1]
		dict['type'] = message[3]
		dict['class'] = message[5]
		dict['time_sent'] = message[-1]
		if(dict['type'])=='image':
			dict['filename'] = message[4]
		if(dict['class']=='group message' or dict['class']=='group invite' or dict['class']=='group update'):
			dict['group name']=message[6]
		pending.append(dict)
	log(f"Pending messages sent to user {username}")
	sock.send(to_send({'command' : 'pending messages', 'messages' : pending}))

def store_message(dict):
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor()
	if(dict['type']=='message'):
		if(dict['class']=='group message' or dict['class']=='group invite' or dict['class']=='group update'):
			cur.execute(f'''
			INSERT INTO 
			INDIVIDUAL_MESSAGES(from_user_name, to_user_name, message_content, message_type, class, groupname, time_sent) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['class']}', '{dict['group name']}', '{dict['time_sent']}')''')
		else:
			cur.execute(f'''
			INSERT INTO 
			INDIVIDUAL_MESSAGES(from_user_name, to_user_name, message_content, message_type, class, time_sent) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['class']}', '{dict['time_sent']}')''')
	elif(dict['type']=='image'):
		if(dict['class']=='group message'):
			cur.execute(f'''
			INSERT INTO 
			INDIVIDUAL_MESSAGES(from_user_name, to_user_name, message_content, message_type, filename, class, groupname, time_sent) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['filename']}', '{dict['class']}', '{dict['group name']}', '{dict['time_sent']}')''')
		elif (dict['class']=='user message'):
			cur.execute(f'''
			INSERT INTO 
			INDIVIDUAL_MESSAGES(from_user_name, to_user_name, message_content, message_type, filename, class, time_sent) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['filename']}', '{dict['class']}', '{dict['time_sent']}')''')
	log("Messages meant for an offline user stored")
	conn.commit()
	cur.close()
	conn.close()

def authenticate(sock, password):
	global validated
	global socket_name
	global name_socket
	global connected_list
	global number

	username = socket_name[sock]
	log(f"Authenticating {username}")
	if(validated[sock] in [0,1]):
		conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
		cur = conn.cursor()
		# cur.execute(f"SELECT password_hash FROM USERS WHERE username LIKE '{username}'")
		# pass_real = cur.fetchall()[0][0]
		# print("Real password of this user: ", pass_real)
		# print("password entered by user: ", password)
		# if(pass_real == password):
		# 	print(f"[DEBUG] {username} authenticated!")
		# 	validated[sock] = 3
		# 	cur.execute(f"UPDATE USERS SET current_server_number = {number} WHERE username = '{username}'")
		# 	send_pending_messages(sock)
		cur.execute(f"SELECT salt FROM USERS WHERE username = '{username}'")
		salt = cur.fetchall()[0][0].encode()
		cur.execute(f"SELECT password_hash FROM USERS WHERE username = '{username}'")
		hash_pw = cur.fetchall()[0][0].encode()
		if crypto.verify_hash(salt, password, hash_pw):
			log("User verified")
			validated[sock] = 3
			log("User connected to the server")
			cur.execute(f"UPDATE USERS SET current_server_number = {number} WHERE username = '{username}'")
			send_pending_messages(sock)
			log("Pending messages sent")
		else:
			log(f"Incorrect password entered by {username}")
			sock.send(to_send({'command' : 're-enter'}))
			validated[sock] += 1
		conn.commit()
		cur.close()
		conn.close()
		return
	
	elif(validated[sock] == 2):
		#entering the password the final 3rd time
		log("user: ", username, " is attempting final login")
		conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
		cur = conn.cursor()
		cur.execute(f"SELECT password_hash FROM USERS WHERE username LIKE '{username}'")
		pass_real = cur.fetchall()[0][0]
		if(pass_real == password):
			log("User verified")
			validated[sock] = 3
			log("User connected to the server")
			sock.send(to_send({'command' : 'password accepted'}))
			cur.execute(f"UPDATE USERS SET current_server_number = {number} WHERE username = '{username}'")
			send_pending_messages(sock)
		else:
			log("Incorrect password entered 3 times, user disconnected")
			sock.send(to_send({'command' : 'error', 'type' : 'wrong password error'}))
			del socket_name[sock]
			del name_socket[username]
			connected_list.remove(sock)
			lb_socket.send(to_send({'command' : 'update count', 'type' : 'decrease'}))
			sock.close()
		conn.commit()
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
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor() 
	# cur.execute(f'''INSERT INTO USERS(username, password_hash, current_server_number) VALUES 
	# ('{username}', '{password}', {number})
	# ''')
	salt = crypto.generate_salt()
	cur.execute(f'''INSERT INTO USERS(username, salt, password_hash, current_server_number) VALUES 
	('{username}', '{salt.decode()}', '{crypto.hash_with_salt(salt, password.encode()).decode()}', {number})
	''')
	log(f"New user {username} added to the database")
	conn.commit()
	cur.close()
	conn.close()
	sock.send(to_send({'command' : 'register for keyServer'}))
	#send_to_all(sock, f"\33[32m\33[1m\r New user {record[(i,p)]} joined the conversation \n\33[0m")
	validated[sock] = 3	


def connect_to_servers(self_port):
	global other_servers_sockets
	for i in range(5001, self_port):
		log("Connecting to previously active servers")
		curr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		curr.bind((ip, i + number * 100))
		curr.connect(('localhost', i))
		print(curr.recv(1024).decode())
		other_servers_sockets.append(curr)


def make_lb_connection():
	global lb_socket
	global other_servers_sockets
	lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	lb_socket.bind((ip, 5000 + 100 * number))
	lb_socket.connect(('localhost', LOAD_BALANCER_PORT))
	log("Server connected to the load balancer")
	other_servers_sockets.append(lb_socket)



def new_connection():
	global other_servers_sockets
	global next_server_ports
	global sock
	log("NEW CONNECTION TO THE SERVER")
	new_conn_socket, addr = sock.accept()
	#the new connection is another server
	if addr[1] in next_server_ports:
		log("New active server connected")
		other_servers_sockets.append(new_conn_socket)
		new_conn_socket.send(("Hey from " + str(port)).encode())
	#the new connection is a client
	else:
		#handle cases
		log("Client connection detected")
		data = new_conn_socket.recv(1024)
		dict = from_recv(data)
		try:
			if dict['command'] == 'first connection' and dict['authentication token'] in tokens:
				log("Token from client authenticated")
				tokens.remove(dict['authentication token'])
				connected_list.append(new_conn_socket)
				lb_socket.send(to_send({'command' : 'update count', 'type' : 'increase'}))
				client_name = dict['username']
				socket_name[new_conn_socket] = client_name
				name_socket[client_name] = new_conn_socket
				#check if the user name received is in the database
				existing_user = False
				conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
				cur = conn.cursor()
				cur.execute(f"SELECT * FROM USERS WHERE username = '{client_name}'")
				if len(cur.fetchall()) > 0: 
					existing_user = True
				cur.close()
				conn.close()
				if(existing_user):
					validated[new_conn_socket] = 0
					new_conn_socket.send(to_send({'command' : 'existing user'}))
				else:
					validated[new_conn_socket] = -1
					new_conn_socket.send(to_send({'command' : 'new user'}))
				log("Appropriate password authentication requested from client")
		except Exception as e:
			log(f"Client side socket closed/error {e}")
			new_conn_socket.send(to_send({'command' : 'error', 'type' : 'wrong authentication token'}))


def load_balancer_token():
	log("Load balancer sending a token")
	#Load balancer sending a token to validate
	token = sock.recv(4096)
	dict = from_recv(token)
	if dict['command'] == 'authentication token':
		tokens.append(dict['token'])
		log(f"token: {token} added to server tokens list")


def msg_from_other_server():
	global sock
	log("Incoming message data from a server")
	#other servers send "user2 - user1 : message", where user2 in connected list
	data = sock.recv(4096)
	dict = from_recv(data)
	try:
		if dict['command'] == 'user-user message':
			user2 = dict['receiver username']
			if user2 in name_socket.keys() and validated[name_socket[user2]] == 3:
				user_sock = name_socket[user2]
				user_sock.send(to_send(dict))
				log(f"User {user2} sent a message")
			else:
				log(f"User {user2} offline, storing message in the database")
				# print("storing messages")
				store_message(dict)
	except:
		pass


def new_password(dict):
	print("[DEBUG] Registering new password...")
	password_enc = dict['encrypted password']
	servers_privkey = crypto.import_key("SERVERS_PRIVKEY.pem")
	password = crypto.decryptRSA(servers_privkey, b64decode(password_enc)).decode()
	print(f"RECEIVED pw {password}")
	add_new_user(sock, password)


def create_group(dict):
	print("[DEBUG] creating group")
	groupname = dict['group name']
	adminname = dict['admin']
	log(f"Group {groupname} creation request from {adminname}")
	list_of_members = dict['member list']
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor()
	cur.execute(f"SELECT * FROM GROUPS WHERE group_name='{groupname}'")

	if(len(cur.fetchall())>0):
		sock.send(to_send({"command":"error", "type":"groupname already exists"}))
		log("Invalid group name")
		return -1
	else:
		cur.execute(f"INSERT INTO GROUPS(group_name,group_admin,group_members) VALUES ('{groupname}', '{adminname}', '{json.dumps(list_of_members)}') ")
		log("GROUP CREATED")
		conn.commit()
	cur.close()
	conn.close()


def add_to_group(dict):
	groupname = dict['group name']
	list_of_members = dict['member list']
	log(f"Request for adding members to {groupname}")
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor()
	cur.execute(f"SELECT * FROM GROUPS WHERE group_name='{groupname}'")
	groupdata = cur.fetchall()[0]

	client_username = socket_name[sock]

	if(groupdata[1]==client_username):
		sock.send(to_send({"command":"admin verified"}))
	else:
		log(f"Bad admin error from {client_username}")
		sock.send(to_send({"command":"error, bad admin"}))
		cur.close()
		conn.close()
		return -1
	
	old_group_members = json.loads(groupdata[2])
	list_of_members2 = []
	for member in list_of_members:
		if(member not in old_group_members):
			list_of_members2.append(member)
	list_of_members2.extend(old_group_members)
	cur.execute(f"UPDATE GROUPS SET group_members='{json.dumps(list_of_members2)}' where group_name='{groupname}' ")
	log("Group member list updated")
	conn.commit()
	cur.close()
	conn.close()


def remove_from_group(dict):
	groupname = dict['group name']
	list_of_members = dict['member list']
	log(f"Request for removing members to {groupname}")
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor()
	cur.execute(f"SELECT * FROM GROUPS WHERE group_name='{groupname}'")
	groupdata = cur.fetchall()[0]

	client_username = socket_name[sock]
	admin = groupdata[1]
	if(admin==client_username):
		pass
	else:
		log(f"Bad admin error from {client_username}")
		sock.send(to_send({"command":"error, bad admin"}))
		cur.close()
		conn.close()
		return -1
	
	old_group_members = json.loads(groupdata[2])
	list_of_members2 = []
	for member in old_group_members:
		if(member not in list_of_members):
			list_of_members2.append(member)
		elif(member==admin):
			list_of_members2.append(member)
	print("[DEBUG] New grp members list:", list_of_members2)
	cur.execute(f"UPDATE GROUPS SET group_members='{json.dumps(list_of_members2)}' where group_name='{groupname}' ")
	log("Group member list updated")
	conn.commit()
	cur.close()
	conn.close()
	sock.send(to_send({"command":"remaining grp members", 'members':list_of_members2}))



def create_message_list(dict):
	message_list = []
	if(dict['class']=='group message'):
		log("Message meant for group received")
		groupname = dict['group name']
		sender = dict['sender username']
		conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
		cur = conn.cursor()
		cur.execute(f"SELECT * FROM GROUPS WHERE group_name = '{groupname}'")
		list_of_members = json.loads(cur.fetchall()[0][2])
		cur.close()
		conn.close()
		if(sender not in list_of_members):
			log(f"Bad member error due to {sender}")
			sock.send(to_send({"command":"error, bad member"}))
			return -1
		else:
			sock.send(to_send({"command":"accepted"}))
		for member in list_of_members:
			if(member!=sender):
				print("preparing message for:", member)
				individual_message = dict.copy()
				individual_message['receiver username'] = member
				message_list.append(individual_message)
	elif dict['class']=='user message' or dict['class']=='group invite' or dict['class']=='group update':
		log("Individual message or group update message received")
		message_list.append(dict)

	return message_list



def handle_message(dict):
	global sock
	print(dict)
	sender = socket_name[sock]
	if sender == dict['sender username']:
		user2 = dict['receiver username']
		message = dict['encrypted message']
		conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
		cur = conn.cursor()
		cur.execute(f"SELECT current_server_number FROM USERS WHERE username = '{user2}'")
		db_data = cur.fetchall()
		valid = False
		if len(db_data) == 0:
			print(f"Message receiver {user2} not found in the database")
			sock.send(to_send({'command' : 'error', 'type' : 'user not found'}))
		else:
			valid = True
			receiver_server = db_data[0][0]
			print(receiver_server)
		cur.close()
		conn.close()
		if valid:
			if receiver_server == number:
				print("Message meant for user connected to the server")
				if user2 in name_socket.keys() and validated[name_socket[user2]] == 3:
					user2_sock = name_socket[user2]
					user2_sock.send(to_send(dict))
				else:
					#store in the database
					store_message(dict)
			else:
				print("Message meant for user connected to other server")
				if receiver_server < number:
					receiver_port = 5000 + receiver_server
				else:
					receiver_port = 5000 + 100 * receiver_server + number
				print("receiver port: ", receiver_port)
				for s in other_servers_sockets:
					ip, r_port = s.getpeername()
					print("r_port: ", r_port)
					if r_port == receiver_port:
						s.send(to_send(dict))
						print("sent message")
		print("Message sent to the appropriate socket")

def handle_socket_closure(e):
	global sock
	global socket_name
	global name_socket
	sender = socket_name[sock]
	log(f"Error occured in connected client: {e}")
	log(f"{sender} removed")
	log("Updating online users count for the load balancer")
	lb_socket.send(to_send({'command' : 'update count', 'type' : 'decrease'}))
	sock.close()
	connected_list.remove(sock)
	del socket_name[sock]
	del name_socket[sender]


LOAD_BALANCER_PORT = 5000
NUM_SERVERS = 5
self_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
self_port = int(sys.argv[1])
ip = 'localhost'
port = int(sys.argv[1])
number = port - 5000
#add self_server_socket to connected_list
self_server_socket.bind((ip, port))
log("Server active on the correct port")
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


next_server_ports = []
for i in range(number + 1, NUM_SERVERS + 1):
	next_server_ports.append(5000 + i * 100 + number)

other_servers_sockets = []

connect_to_servers(self_port)

print(next_server_ports)
make_lb_connection()

#connect to prev running servers with NEW SOCKETS on the SAME PORT


while True:
	rlist, wlist, elist = select.select(connected_list + other_servers_sockets, [], [])
	for sock in rlist:
		if sock == self_server_socket:
			new_connection()
		elif sock == lb_socket:
			load_balancer_token()

		elif sock in other_servers_sockets:
			msg_from_other_server()
		else:
			#a connected user sending a message
			log("Client side message to the server")
			#case 1: a user trying to get autheticated
			try:
				dict = from_recv(sock.recv(4096))
				if dict['command'] == 'new password':
					# password = dict['password']
					# print(f"RECEIVED pw {password}")
					# add_new_user(sock, password)
					new_password(dict)
				
				elif dict['command'] == 'password authenticate':
					password = dict['password']
					print(f"RECEVIED pw-auth {password}")
					authenticate(sock, password)
				
				elif dict['command'] == 'create group':
					create_group(dict)
					
				elif dict['command'] == 'add to group':
					add_to_group(dict)

				elif dict['command'] == 'remove from group':
					remove_from_group(dict)
					
				elif dict['command'] == 'user-user message':
					#user2 - message
					message_list = create_message_list(dict)
					print(message_list)
					if(message_list==-1):
						continue

					for dict in message_list:				
						handle_message(dict)
			
				elif dict["command"] == "password authenticate lvl1":
					log("Password authentication")
					aes_key, aes_iv = crypto.gen_AES_key_iv()
					sock.send(to_send({"command": "password authenticate lvl2", "aes_key": encryptData(aes_key, dict["username"], True),"aes_iv": encryptData(aes_iv, dict["username"], True)}))
					response = from_recv(sock.recv(4096))
					assert response["command"] == "password authenticate lvl3"
					password = crypto.decryptAES(aes_key, aes_iv, b64decode(response["encrypted password"]))
					authenticate(sock, password)


			except Exception as e:
				handle_socket_closure(e)

				


					

			
				






