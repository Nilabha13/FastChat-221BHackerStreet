import socket, select
import psycopg2
import sys
from utilities import *
from constants import *
import crypto
import re
import os
from base64 import b64encode, b64decode


def encryptData(data, to_username, is_image=False, type = 'fastchatter'):
	"""
	This function is meant to encrypt a message for a username. It takes into account whether the message is a group message or an individual 
	message, a text message or an image and also for whom the message is meant.

	:param data: The message to be encrypted
	:type data: string
	:param to_username: The username of the receiver. With whose public key the encryption is to be done. Might be user or group
	:type to_username: string
	:param is_image: Whether the data passed is image data or not. Default = False
	:type is_image: bool
	:param type: Whether the message is meant for a fastchatter or a group. Default='fastchatter'
	:type type: string
	"""
	global prev_users
	if not is_image:
		data = data.encode()
	if to_username not in prev_users:
		ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ks.connect(('localhost', KEYSERVER_PORT))
		log(f"Connecting to the key server for pub_key of {to_username}")
		ks.send(to_send({"command": "RETRIEVE", "username": to_username, 'type':type}))
		ks_response = from_recv(ks.recv(4096))
		if ks_response["command"] == "PUBKEY":
			
			to_user_pubkey = crypto.str_to_key(ks_response["pubkey"])
			signature = b64decode(ks_response["signature"].encode())
			ks_pubkey = crypto.import_key(os.path.join("keys", "server_keys", "KEYSERVER_PUBKEY.pem"))

			if not crypto.verify_signature(ks_pubkey, ks_response['pubkey'].encode(), signature):
				log("Malicious tampering with keyserver!")
				raise "Malicious tampering with keyserver!"
			create_dirs_if_not_exist_recursive(["keys", "server_cached_keys"])
			crypto.export_key(to_user_pubkey, os.path.join("keys", "server_cached_keys", f"{to_username}_pub_key.pem"))
			prev_users.append(to_username)
			log(f"Public key of {to_username} successfully retrieved")
			return b64encode(crypto.encryptRSA(to_user_pubkey, data)).decode()
		else:
			log("Keyserver error")
	else:
		to_user_pubkey = crypto.import_key(os.path.join("keys", "server_cached_keys", f"{to_username}_pub_key.pem"))
		return b64encode(crypto.encryptRSA(to_user_pubkey, data)).decode()

def send_pending_messages(sock):
	"""
	This function is called when an existing client has just come online and signed in. In such a situation, we wish to send messages that 
	were stored with the client as the receiver to them. These messages would have been stored as they were received when the client was offline 
	but they are sent to them now.

	:param sock: The socket over which to send the messages
	:type sock: socket.socket	
	"""
	global socket_name
	# a user is authenticated, send him stored messages from the database
	username = socket_name[sock]
	pending = []
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor()
	cur.execute(f"SELECT * FROM MESSAGES WHERE to_user_name = '{username}'")
	messages = cur.fetchall()
	cur.execute(f"DELETE FROM MESSAGES WHERE to_user_name = '{username}'")
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
	# split large data here
	my_send(sock, to_send({'command' : 'pending messages', 'messages' : pending}))
	log(f"Pending messages sent to user {username}")

def store_message(dict):
	"""
	This function is called when a message has come to the server for a client but the client is offline. The server at this point stores the 
	message in a database and waits to send the message to the client when they come back online. It stores all details of the message 
	including whether it is a group message, an image etc.

	:param dict: This is the message that has been received by the server which needs to be stored in the database
	:type dict: dict
	
	"""
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor()
	if(dict['type']=='message'):
		if(dict['class']=='group message' or dict['class']=='group invite' or dict['class']=='group update'):
			cur.execute(f'''
			INSERT INTO 
			MESSAGES(from_user_name, to_user_name, message_content, message_type, class, groupname, time_sent) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['class']}', '{dict['group name']}', '{dict['time_sent']}')''')
		else:
			cur.execute(f'''
			INSERT INTO 
			MESSAGES(from_user_name, to_user_name, message_content, message_type, class, time_sent) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['class']}', '{dict['time_sent']}')''')
	elif(dict['type']=='image'):
		if(dict['class']=='group message'):
			cur.execute(f'''
			INSERT INTO 
			MESSAGES(from_user_name, to_user_name, message_content, message_type, filename, class, groupname, time_sent) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['filename']}', '{dict['class']}', '{dict['group name']}', '{dict['time_sent']}')''')
		elif (dict['class']=='user message'):
			cur.execute(f'''
			INSERT INTO 
			MESSAGES(from_user_name, to_user_name, message_content, message_type, filename, class, time_sent) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['filename']}', '{dict['class']}', '{dict['time_sent']}')''')
	log(f"Messages meant for offline user {dict['receiver username']} stored")
	conn.commit()
	cur.close()
	conn.close()

def authenticate(sock, password):
	"""
	This function is meant to authenticate the password of the client. It is called when an existing user is trying to sign in and they have 
	entered their password. This password is authenticated based on what is stored in the database. A user has only 3 attempts to get the password 
	right, otherwise they are signed off and have to restart.

	:param sock: The socket object conecting to the client. Need to communicate with it to get the password, send back messages
	:type sock: socket.socket
	:param password: The password entered by the user.
	:type password: str

	"""
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
		cur.execute(f"SELECT salt FROM USERS WHERE username = '{username}'")
		salt = cur.fetchall()[0][0].encode()
		cur.execute(f"SELECT password_hash FROM USERS WHERE username = '{username}'")
		hash_pw = cur.fetchall()[0][0].encode()
		if crypto.verify_hash(salt, password, hash_pw):
			validated[sock] = 3
			cur.execute(f"UPDATE USERS SET current_server_number = {number} WHERE username = '{username}'")
			send_pending_messages(sock)
		else:
			# log(f"Incorrect password entered by {username}")
			my_send(sock, to_send({'command' : 're-enter'}))
			validated[sock] += 1
		conn.commit()
		cur.close()
		conn.close()
		return
	
	elif(validated[sock] == 2):
		# entering the password the final 3rd time
		# log("user: ", username, " is attempting final login")
		conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
		cur = conn.cursor()
		cur.execute(f"SELECT password_hash FROM USERS WHERE username LIKE '{username}'")
		pass_real = cur.fetchall()[0][0]
		if(pass_real == password):
			validated[sock] = 3
			log(f"NEW USER {username} CONNECTED TO THE SERVER")
			my_send(sock, to_send({'command' : 'password accepted'}))
			cur.execute(f"UPDATE USERS SET current_server_number = {number} WHERE username = '{username}'")
			send_pending_messages(sock)
		else:
			my_send(sock, to_send({'command' : 'error', 'type' : 'wrong password error'}))
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
	"""Adds a new user to the database.

	:param sock: The socket through which the server is connected to the client user.
	:type sock: socket.socket
	:param password: The password entered by the user.
	:type password: str
	"""
	global validated
	global socket_name
	global name_socket
	global connected_list
	global number
	username = socket_name[sock]
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor() 
	salt = crypto.generate_salt()
	cur.execute(f'''INSERT INTO USERS(username, salt, password_hash, current_server_number) VALUES 
	('{username}', '{salt.decode()}', '{crypto.hash_with_salt(salt, password.encode()).decode()}', {number})
	''')
	conn.commit()
	cur.close()
	conn.close()
	log(f"NEW USER {username} CONNECTED TO THE SERVER")
	my_send(sock, to_send({'command' : 'register for keyServer'}))
	validated[sock] = 3	


def connect_to_servers(self_port):
	"""Established a connection with the other servers.
	"""
	global other_servers_sockets
	for i in range(5001, self_port):
		log(f"CONNECTED TO THE SERVER ON PORT {i}")
		curr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		curr.bind((ip, i + number * 100))
		curr.connect(('localhost', i))
		other_servers_sockets.append(curr)


def make_lb_connection():
	"""Makes a connection with the load balancer.
	"""
	global lb_socket
	global other_servers_sockets
	lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	lb_socket.bind((ip, 5000 + 100 * number))
	lb_socket.connect(('localhost', LOAD_BALANCER_PORT))
	log("CONNECTED TO THE LOAD BALANCER")
	other_servers_sockets.append(lb_socket)



def new_connection():
	"""Handles a new incoming connection to the server.
	"""
	global other_servers_sockets
	global next_server_ports
	global sock
	new_conn_socket, addr = sock.accept()
	# the new connection is another server
	if addr[1] in next_server_ports:
		log(f"ACCEPTED CONNECTION FROM THE SERVER ON PORT {addr[1]}")
		other_servers_sockets.append(new_conn_socket)
	# the new connection is a client
	else:
		# handle cases
		data = my_recv(new_conn_socket, 4096)
		dict = from_recv(data)
		try:
			if dict['command'] == 'first connection' and dict['authentication token'] in tokens:
				tokens.remove(dict['authentication token'])
				connected_list.append(new_conn_socket)
				lb_socket.send(to_send({'command' : 'update count', 'type' : 'increase'}))
				client_name = dict['username']
				socket_name[new_conn_socket] = client_name
				name_socket[client_name] = new_conn_socket
				# check if the user name received is in the database
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
					my_send(new_conn_socket, to_send({'command' : 'existing user'}))
				else:
					validated[new_conn_socket] = -1
					my_send(new_conn_socket, to_send({'command' : 'new user'}))
		except Exception as e:
			log(f"Client side socket closed/error {e}")
			handle_socket_closure(e)


def load_balancer_token():
	"""Accepts a token from the load balancer.
	"""
	log("TOKEN from load balancer received")
	# Load balancer sending a token to validate
	token = sock.recv(4096)
	dict = from_recv(token)
	if dict['command'] == 'authentication token':
		tokens.append(dict['token'])


def msg_from_other_server():
	"""Handles the reception of a message from another server.
	"""
	global sock
	port = sock.getpeername()[1]
	log(f"SERVER at {port} sent a message")
	# other servers send "user2 - user1 : message", where user2 in connected list
	data = my_recv(sock, 4096)
	dict = from_recv(data)
	user2 = dict['receiver username']
	try:
		if dict['command'] == 'user-user message':
			if user2 in name_socket.keys() and validated[name_socket[user2]] == 3:
				user_sock = name_socket[user2]
				my_send(user_sock, to_send(dict))
				log(f"SERVER SENT A MESSAGE TO CLIENT {user2}")
			else:
				log(f"{user2} OFFLINE, STORING A MESSAGE")
				store_message(dict)
	except:
		handle_socket_closure(name_socket[user2])


def new_password(dict):
	"""Registers the password of a newly added user.

	:param dict: The dictionary sent to the server (refer to protocol)
	:type dict: dict
	"""
	password_enc = dict['encrypted password']
	servers_privkey = crypto.import_key(os.path.join("keys", "server_keys", "SERVERS_PRIVKEY.pem"))
	password = crypto.decryptRSA(servers_privkey, b64decode(password_enc)).decode()
	add_new_user(sock, password)


def create_group(dict):
	"""Creates a new group.

	:param dict: The dictionary of parameters (refer to protocol)
	:type dict: dict
	:return: If the group was created
	:rtype: int
	"""
	groupname = dict['group name']
	adminname = dict['admin']
	log(f"GROUP {groupname} creation request from {adminname}")
	list_of_members = dict['member list']
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor()
	cur.execute(f"SELECT * FROM GROUPS WHERE group_name='{groupname}'")

	if(len(cur.fetchall())>0):
		my_send(sock, to_send({"command":"error", "type":"groupname already exists"}))
		log("INVALID GROUP NAME")
		return -1
	else:
		cur.execute(f"INSERT INTO GROUPS(group_name,group_admin,group_members) VALUES ('{groupname}', '{adminname}', '{json.dumps(list_of_members)}') ")
		log("GROUP CREATED")
		conn.commit()
	cur.close()
	conn.close()


def add_to_group(dict):
	"""Adds members to the group.

	:param dict: The dictionary of parameters (refer to protocol)
	:type dict: dict
	:return: If the update was successful
	:rtype: int
	"""
	groupname = dict['group name']
	list_of_members = dict['member list']
	log(f"Request for adding members to {groupname}")
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor()
	cur.execute(f"SELECT * FROM GROUPS WHERE group_name='{groupname}'")
	groupdata = cur.fetchall()[0]

	client_username = socket_name[sock]

	if(groupdata[1]==client_username):
		my_send(sock, to_send({"command":"admin verified"}))
	else:
		log(f"BAD ADMIN error from {client_username}")
		my_send(sock, to_send({"command":"error, bad admin"}))
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
	conn.commit()
	cur.close()
	conn.close()


def remove_from_group(dict):
	"""Remove members from the group.

	:param dict: The dictionary of parameters (refer to protocol)
	:type dict: dict
	:return: If the removal was successful
	:rtype: int
	"""
	groupname = dict['group name']
	list_of_members = dict['member list']
	log(f"Request for removing members from {groupname}")
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor()
	cur.execute(f"SELECT * FROM GROUPS WHERE group_name='{groupname}'")
	groupdata = cur.fetchall()[0]

	client_username = socket_name[sock]
	admin = groupdata[1]
	if(admin==client_username):
		pass
	else:
		log(f"BAD ADMIN error from {client_username}")
		my_send(sock, to_send({"command":"error, bad admin"}))
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
	cur.execute(f"UPDATE GROUPS SET group_members='{json.dumps(list_of_members2)}' where group_name='{groupname}' ")
	conn.commit()
	cur.close()
	conn.close()
	my_send(sock, to_send({"command":"remaining grp members", 'members':list_of_members2}))



def create_message_list(dict):
	"""Handles the creation of a list of messages if required.

	:param dict: The dictionary of parameters (refer to protocol)
	:type dict: dict
	:return: The list of messages
	:rtype: list
	"""
	global sock
	sender = socket_name[sock]
	if sender != dict['sender username']:
		return []
	message_list = []
	if(dict['class']=='group message'):
		groupname = dict['group name']
		sender = dict['sender username']
		conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
		cur = conn.cursor()
		cur.execute(f"SELECT * FROM GROUPS WHERE group_name = '{groupname}'")
		list_of_members = json.loads(cur.fetchall()[0][2])
		cur.close()
		conn.close()
		if(sender not in list_of_members):
			log(f"BAD GROUP MEMBER error due to {sender}")
			my_send(sock, to_send({"command":"error, bad member"}))
			return -1
		else:
			my_send(sock, to_send({"command":"accepted"}))
		for member in list_of_members:
			if(member!=sender):
				individual_message = dict.copy()
				individual_message['receiver username'] = member
				message_list.append(individual_message)
	elif dict['class']=='user message' or dict['class']=='group invite' or dict['class']=='group update':
		message_list.append(dict)

	return message_list



def handle_message(dict):
	"""Handles the transfer of a message from one client to another.

	:param dict: The dictionary of parameters (refer to protocol)
	:type dict: dict
	"""
	user2 = dict['receiver username']
	conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
	cur = conn.cursor()
	cur.execute(f"SELECT current_server_number FROM USERS WHERE username = '{user2}'")
	db_data = cur.fetchall()
	valid = False
	if len(db_data) == 0:
		my_send(sock, to_send({'command' : 'error', 'type' : 'user not found'}))
	else:
		valid = True
		receiver_server = db_data[0][0]
	cur.close()
	conn.close()
	if valid:
		if receiver_server == number:
			if user2 in name_socket.keys() and validated[name_socket[user2]] == 3:
				user2_sock = name_socket[user2]
				my_send(user2_sock, to_send(dict))
				log(f"SERVER SENT A MESSAGE TO CLIENT {user2}")
			else:
				# store in the database
				store_message(dict)
		else:
			if receiver_server < number:
				receiver_port = 5000 + receiver_server
			else:
				receiver_port = 5000 + 100 * receiver_server + number
			for s in other_servers_sockets:
				ip, r_port = s.getpeername()
				if r_port == receiver_port:
					my_send(s, to_send(dict))
					log(f"FORWARDED A MESSAGE TO THE SERVER ON PORT {r_port}")

def handle_socket_closure(e):
	"""Handles the closing of a server-user socket.

	:param e: The exception
	:type e: Exception
	"""
	global sock
	global socket_name
	global name_socket
	sender = socket_name[sock]
	log(f"{sender} REMOVED due to {e}")
	lb_socket.send(to_send({'command' : 'update count', 'type' : 'decrease'}))
	sock.close()
	connected_list.remove(sock)
	del socket_name[sock]
	del name_socket[sender]


if __name__ == "__main__":
	LOAD_BALANCER_PORT = 5000
	NUM_SERVERS = 5
	self_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	self_port = int(sys.argv[1])
	ip = 'localhost'
	port = int(sys.argv[1])
	number = port - 5000

	create_dirs_if_not_exist_recursive(["logs", "servers_logs"])
	logfd = open(os.path.join("logs", "servers_logs", f"server{sys.argv[1]}.log"), 'w')
	def log(msg):
		log_to_file(msg, logfd)


	prev_users = []
	r = re.compile(f"(.*)(_pub_key.pem)")
	create_dirs_if_not_exist_recursive(["keys", "server_cached_keys"])
	for i in os.listdir(os.path.join("keys", "server_cached_keys")):
		match = re.search(r, i)
		if match != None:
			prev_users.append(match.group(1))

	# add self_server_socket to connected_list
	self_server_socket.bind((ip, port))
	log(f"SERVER ACTIVE ON PORT {port}")
	self_server_socket.listen(10)

	# a dictionary with client names
	socket_name = {}
	name_socket = {}
	# a dictionary with validated status of connections
	validated = {}
	tokens = ["default"]
	connected_list = []
	connected_list.append(self_server_socket)
	# connect to load balancer with a new socket ON THE SAME PORT


	next_server_ports = []
	for i in range(number + 1, NUM_SERVERS + 1):
		next_server_ports.append(5000 + i * 100 + number)

	other_servers_sockets = []

	connect_to_servers(self_port)

	make_lb_connection()

	# connect to prev running servers with NEW SOCKETS on the SAME PORT


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
				# a connected user sending a message
				log("Client side command to the server")
				# case 1: a user trying to get autheticated
				try:
					dict = from_recv(my_recv(sock, 4096))
					if dict['command'] == 'new password':
						new_password(dict)
					
					elif dict['command'] == 'password authenticate':
						password = dict['password']
						authenticate(sock, password)
					
					elif dict['command'] == 'create group':
						create_group(dict)
						
					elif dict['command'] == 'add to group':
						add_to_group(dict)

					elif dict['command'] == 'remove from group':
						remove_from_group(dict)
						
					elif dict['command'] == 'user-user message':
						# user2 - message
						client = socket_name[sock]
						log(f"CLIENT {client} SENT A MESSAGE TO THE SERVER")
						message_list = create_message_list(dict)
						for message in message_list:				
							handle_message(message)
				
					elif dict["command"] == "password authenticate lvl1":
						aes_key, aes_iv = crypto.gen_AES_key_iv()
						my_send(sock, to_send({"command": "password authenticate lvl2", "aes_key": encryptData(aes_key, dict["username"], True),"aes_iv": encryptData(aes_iv, dict["username"], True)}))
						response = from_recv(my_recv(sock, 4096))
						assert response["command"] == "password authenticate lvl3"
						password = crypto.decryptAES(aes_key, aes_iv, b64decode(response["encrypted password"]))
						authenticate(sock, password)

				except Exception as e:
					handle_socket_closure(e)

				


					

			
				






