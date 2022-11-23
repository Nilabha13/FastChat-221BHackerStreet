import socket, select
import psycopg2
import sys
from utilities import *
from constants import *
import crypto
import re
import os

logfd = open(f"server{sys.argv[1]}.log", 'w')
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
		ks.send(to_send({"command": "RETRIEVE", "username": to_username, 'type':type}))
		ks_response = from_recv(ks.recv(4096))
		if ks_response["command"] == "PUBKEY":
			print("Inside")
			to_user_pubkey = crypto.str_to_key(ks_response["pubkey"])
			signature = b64decode(ks_response["signature"].encode())
			ks_pubkey = crypto.import_key("KEYSERVER_PUBKEY.pem")
			print("Let's go")
			if not crypto.verify_signature(ks_pubkey, ks_response['pubkey'].encode(), signature):
				print("Hi! It's me!")
				# fp(signature)
				# fp(crypto.decryptRSA(ks_pubkey, signature))
				# fp(crypto.sha256(ks_response['pubkey'].encode()).digest())
				raise "Malicious tampering with keyserver!"
			print("Successfully returning...")
			crypto.export_key(to_user_pubkey, f"mykeys/servers_{to_username}_pub_key.pem")
			prev_users.append(to_username)
			return b64encode(crypto.encryptRSA(to_user_pubkey, data)).decode()
		else:
			print("[ERROR] Key server returned an error!")
	else:
		print("[DEBUG] Accessing key cache")
		to_user_pubkey = crypto.import_key(f"mykeys/servers_{to_username}_pub_key.pem")
		return b64encode(crypto.encryptRSA(to_user_pubkey, data)).decode()

def send_pending_messages(sock):
	global socket_name
	# a user is authenticated, send him stored messages from the database
	username = socket_name[sock]
	pending = []
	conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
	cur = conn.cursor()
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
		print("[DEBUG] pending message getting ready")
		if(dict['type'])=='image':
			dict['filename'] = message[4]
		if(dict['class']=='group message' or dict['class']=='group invite'):
			dict['group name']=message[6]
		print("[DEBUG] pending message getting ready")
		pending.append(dict)
	print(f"[DEBUG] Pending messages sent")
	sock.send(to_send({'command' : 'pending messages', 'messages' : pending}))

def store_message(dict):
	conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
	cur = conn.cursor()
	if(dict['type']=='message'):
		if(dict['class']=='group message' or dict['class']=='group invite'):
			cur.execute(f'''
			INSERT INTO 
			INDIVIDUAL_MESSAGES(from_user_name, to_user_name, message_content, message_type, class, groupname) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['class']}', '{dict['group name']}')''')
		else:
			cur.execute(f'''
			INSERT INTO 
			INDIVIDUAL_MESSAGES(from_user_name, to_user_name, message_content, message_type, class) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['class']}')''')
	elif(dict['type']=='image'):
		if(dict['class']=='group message'):
			cur.execute(f'''
			INSERT INTO 
			INDIVIDUAL_MESSAGES(from_user_name, to_user_name, message_content, message_type, filename, class, groupname) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['filename']}', '{dict['class']}', '{dict['group name']}')''')
		elif (dict['class']=='user message'):
			cur.execute(f'''
			INSERT INTO 
			INDIVIDUAL_MESSAGES(from_user_name, to_user_name, message_content, message_type, filename, class) 
			VALUES('{dict['sender username']}', '{dict['receiver username']}', '{dict['encrypted message']}', '{dict['type']}', '{dict['filename']}', '{dict['class']}')''')
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
	if(validated[sock] in [0,1]):
		conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
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
			print(f"[DEBUG] {username} authenticated!")
			validated[sock] = 3
			cur.execute(f"UPDATE USERS SET current_server_number = {number} WHERE username = '{username}'")
			send_pending_messages(sock)
		else:
			sock.send(to_send({'command' : 're-enter'}))
			validated[sock] += 1
		conn.commit()
		cur.close()
		conn.close()
		return
	
	elif(validated[sock] == 2):
		#entering the password the final 3rd time
		print("user: ", username, " is attempting final login ", password)
		conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
		cur = conn.cursor()
		cur.execute(f"SELECT password_hash FROM USERS WHERE username LIKE '{username}'")
		pass_real = cur.fetchall()[0][0]
		print("Real password of this user: ", pass_real)
		print("password entered by user: ", password)
		if(pass_real == password):
			validated[sock] = 3
			sock.send(to_send({'command' : 'password accepted'}))
			cur.execute(f"UPDATE USERS SET current_server_number = {number} WHERE username = '{username}'")
			send_pending_messages(sock)
		else:
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
	print("user: ", username, " has entered password: ", password)
	conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
	cur = conn.cursor() 
	# cur.execute(f'''INSERT INTO USERS(username, password_hash, current_server_number) VALUES 
	# ('{username}', '{password}', {number})
	# ''')
	salt = crypto.generate_salt()
	cur.execute(f'''INSERT INTO USERS(username, salt, password_hash, current_server_number) VALUES 
	('{username}', '{salt.decode()}', '{crypto.hash_with_salt(salt, password.encode()).decode()}', {number})
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
						lb_socket.send(to_send({'command' : 'update count', 'type' : 'increase'}))
						client_name = dict['username']
						socket_name[new_conn_socket] = client_name
						name_socket[client_name] = new_conn_socket
						#check if the user name received is in the database
						existing_user = False
						conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
						cur = conn.cursor()
						cur.execute(f"SELECT * FROM USERS WHERE username = '{client_name}'")
						if len(cur.fetchall()) > 0: 
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
					print("[DEBUG] user message arrived for user:", dict['receiver username'])
					user2 = dict['receiver username']
					if user2 in name_socket.keys() and validated[name_socket[user2]] == 3:
						user_sock = name_socket[user2]
						user_sock.send(to_send(dict))
					else:
						print("storing messages")
						store_message(dict)
			except:
				pass
		else:
			#a connected user sending a message
			#case 1: a user trying to get autheticated
			try:
				dict = from_recv(sock.recv(4096))
				if dict['command'] == 'new password':
					# password = dict['password']
					# print(f"RECEIVED pw {password}")
					# add_new_user(sock, password)
					print("[DEBUG] Registering new password...")
					password_enc = dict['encrypted password']
					servers_privkey = crypto.import_key("SERVERS_PRIVKEY.pem")
					password = crypto.decryptRSA(servers_privkey, b64decode(password_enc)).decode()
					print(f"RECEIVED pw {password}")
					add_new_user(sock, password)
				
				elif dict['command'] == 'password authenticate':
					password = dict['password']
					print(f"RECEVIED pw-auth {password}")
					authenticate(sock, password)
				
				elif dict['command'] == 'create group':
					print("[DEBUG] creating group")
					groupname = dict['group name']
					adminname = dict['admin']
					list_of_members = dict['member list']
					conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
					cur = conn.cursor()
					cur.execute(f"SELECT * FROM GROUPS WHERE group_name='{groupname}'")

					if(len(cur.fetchall())>0):
						sock.send(to_send({"command":"error", "type":"groupname already exists"}))
						print("[DEBUG] Existing group name")
						continue
					else:
						cur.execute(f"INSERT INTO GROUPS(group_name,group_admin,group_members) VALUES ('{groupname}', '{adminname}', '{json.dumps(list_of_members)}') ")
						conn.commit()
					cur.close()
					conn.close()
					
				elif dict['command'] == 'add to group':
					print("[DEBUG] adding members to group")
					groupname = dict['group name']
					list_of_members = dict['member list']
					conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
					cur = conn.cursor()
					cur.execute(f"SELECT * FROM GROUPS WHERE group_name='{groupname}'")
					groupdata = cur.fetchall()[0]

					client_username = socket_name[sock]

					if(groupdata[1]==client_username):
						sock.send(to_send({"command":"admin verified"}))
					else:
						sock.send(to_send({"command":"error, bad admin"}))
						cur.close()
						conn.close()
						continue
					
					old_group_members = json.loads(groupdata[2])
					list_of_members2 = []
					for member in list_of_members:
						if(member not in old_group_members):
							list_of_members2.append(member)
					list_of_members2.extend(old_group_members)
					print("[DEBUG] New grp members list:", list_of_members2)
					cur.execute(f"UPDATE GROUPS SET group_members='{json.dumps(list_of_members2)}' where group_name='{groupname}' ")
					conn.commit()
					cur.close()
					conn.close()



				elif dict['command'] == 'remove from group':
					print("[DEBUG] removing members from group")
					groupname = dict['group name']
					list_of_members = dict['member list']
					conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
					cur = conn.cursor()
					cur.execute(f"SELECT * FROM GROUPS WHERE group_name='{groupname}'")
					groupdata = cur.fetchall()[0]

					client_username = socket_name[sock]

					if(groupdata[1]==client_username):
						pass
					else:
						sock.send(to_send({"command":"error, bad admin"}))
						cur.close()
						conn.close()
						continue
					
					old_group_members = json.loads(groupdata[2])
					list_of_members2 = []
					for member in old_group_members:
						if(member not in list_of_members):
							list_of_members2.append(member)
					print("[DEBUG] New grp members list:", list_of_members2)
					cur.execute(f"UPDATE GROUPS SET group_members='{json.dumps(list_of_members2)}' where group_name='{groupname}' ")
					conn.commit()
					cur.close()
					conn.close()
					sock.send(to_send({"command":"remaining grp members", 'members':list_of_members2}))
					




				elif dict['command'] == 'user-user message':
					print("[DEBUG] received user-user message")
					#user2 - message
					message_list = []
					if(dict['class']=='group message'):
						print("[DEBUG] group message recieved")
						groupname = dict['group name']
						sender = dict['sender username']
						conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
						cur = conn.cursor()
						cur.execute(f"SELECT * FROM GROUPS WHERE group_name = '{groupname}'")
						list_of_members = json.loads(cur.fetchall()[0][2])
						cur.close()
						conn.close()
						if(sender not in list_of_members):
							sock.send(to_send({"command":"error, bad member"}))
							continue
						else:
							sock.send(to_send({"command":"accepted"}))
						for member in list_of_members:
							if(member!=sender):
								print("preparing message for:", member)
								individual_message = dict.copy()
								individual_message['receiver username'] = member
								message_list.append(individual_message)
					elif dict['class']=='user message' or dict['class']=='group invite':
						print("[DEBUG] individual message recieved")
						message_list.append(dict)

					for dict in message_list:					
						sender = socket_name[sock]
						if sender == dict['sender username']:
							user2 = dict['receiver username']
							message = dict['encrypted message']
							print("sending message, sender:", sender, "receiver:", user2)
							conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
							cur = conn.cursor()
							cur.execute(f"SELECT current_server_number FROM USERS WHERE username = '{user2}'")
							db_data = cur.fetchall()
							valid = False
							if len(db_data) == 0:
								print("user:",user2,"not found")
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
										store_message(dict)
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
			
				elif dict["command"] == "password authenticate lvl1":
					print(["[DEBUG] Authenticating password..."])
					aes_key, aes_iv = crypto.gen_AES_key_iv()
					print("[DEBUG] Sedning AES KEY:")
					print(encryptData(aes_key, dict["username"], True))
					sock.send(to_send({"command": "password authenticate lvl2", "aes_key": encryptData(aes_key, dict["username"], True),"aes_iv": encryptData(aes_iv, dict["username"], True)}))
					response = from_recv(sock.recv(4096))
					assert response["command"] == "password authenticate lvl3"
					print("[DEBUG] Received encrypted password")
					password = crypto.decryptAES(aes_key, aes_iv, b64decode(response["encrypted password"]))
					print("[DEBUG] Password decrypted")
					authenticate(sock, password)


			except Exception as e:
				sender = socket_name[sock]
				print("Eror occured in connected client:", e)
				print(f"{sender} removed")
				lb_socket.send(to_send({'command' : 'update count', 'type' : 'decrease'}))
				sock.close()
				connected_list.remove(sock)
				del socket_name[sock]
				del name_socket[sender]

				


					

			
				






