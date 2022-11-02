import socket, select
import psycopg2
import sys

port = int(sys.argv[1])

#read img as bytes, convert to base 64(b64 encode), decode bytes to string, send as json. Read back as json, encode string to bytes, base64 decode() to get back img.

#Function to send message to all connected clients
def send_to_all (sock, message):
	global connected_list
	global validated
	#Message not forwarded to server and sender itself
	for socket in connected_list:
		if socket != server_socket and socket != sock :
			try :
				i,p = socket.getpeername()
				if(validated[(i,p)]==6):
					socket.send(message.encode())
			except :
				# if connection not available
				socket.close()
				connected_list.remove(socket)

# Function to send message to a single user
def send_to_one(sender_socket, message, receiver_user):
	found = False
	for socket in connected_list:
		if socket != server_socket and socket != sender_socket:
			ip, port = socket.getpeername()
			if record[(ip, port)] == receiver_user:
				found = True
				receiver_socket = socket
				break
	if not found:
		try:
			sender_socket.send("Receiver not found, try again\n".encode())
		except:
			sender_socket.close()
			connected_list.remove(sender_socket)
	else:
		try:
			receiver_socket.send(message.encode())
		except:
			receiver_socket.close()
			connected_list.remove(receiver_socket)


def authenticate(sock, i, p, password):
	global validated
	global record
	global connected_list

	if(validated[(i,p)] in [0,1]):
		conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="Ameya563")
		cur = conn.cursor()
		cur.execute(f"SELECT password_hash FROM USERS WHERE username LIKE '{record[(i,p)]}'")
		pass_real = cur.fetchall()[0][0]
		print("Real password of this user: ", pass_real)
		print("password entered by user: ", password)
		if(pass_real==password):
			validated[(i,p)] = 6
			sock.send("Your password is validated! Welcome back to the chat room!\n".encode())
			send_to_all(sock, f"\33[32m\33[1m\r Existing user {record[(i,p)]} joined the conversation \n\33[0m")
		else:
			sock.send("Wrong password! Re-enter\n".encode())
			print("reached here 1")
			validated[(i,p)]+=1
		cur.close()
		conn.close()
		print("reached here 2")
		return
	
	elif(validated[(i,p)]==2):
		print("user: ", record[(i,p)], " is attempting final login ", password)
		conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="Ameya563")
		cur = conn.cursor()
		cur.execute(f"SELECT password_hash FROM USERS WHERE username LIKE '{record[(i,p)]}'")
		pass_real = cur.fetchall()[0][0]
		print("Real password of this user: ", pass_real)
		print("password entered by user: ", password)
		if(pass_real==password):
			validated[(i,p)] = 6
			sock.send("Your password is validated! Welcome back to the chat room!\n".encode())
			send_to_all(sock, f"\33[32m\33[1m\r Existing user {record[(i,p)]} joined the conversation \n\33[0m")
		else:
			sock.send("Wrong password too may times!\n".encode())
			del record[(i,p)]
			del validated[(i,p)]
			connected_list.remove(sock)
			sock.close()
		cur.close()
		conn.close()
		return

def add_new_user(sock, i, p, password):
	server_ip, server_port = sock.getsockname()
	print("user: ", record[(i,p)], " has entered password: ", password)
	conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="Ameya563")
	cur = conn.cursor() 
	cur.execute("SELECT COUNT(*) FROM USERS")
	count = cur.fetchall()[0][0]
	print("number of users here yet: ", count)

	cur.execute(f"""INSERT INTO USERS(user_id, username, password_hash, current_server_port) VALUES 
	({count+1}, '{record[(i,p)]}', '{password}', {server_port})
	""")
	print("data insertions done!")
	conn.commit()
	cur.close()
	conn.close()
	sock.send("Your password is recieved! Welcome to chat room!\n".encode())
	send_to_all(sock, f"\33[32m\33[1m\r New user {record[(i,p)]} joined the conversation \n\33[0m")
	validated[(i,p)]=6		
					
if __name__ == "__main__":
	name=""
	#dictionary to store address corresponding to username
	record={}
	validated = {}
	# List to keep track of socket descriptors
	connected_list = []
	buffer = 4096
	# port = 5004

	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	server_socket.bind(("localhost", port))
	server_socket.listen(10) #listen atmost 10 connection at one time

	# Add server socket to the list of readable connections
	connected_list.append(server_socket)
	
	print("\33[32m \t\t\t\tSERVER WORKING \33[0m") 

	while 1:
		# Get the list sockets which are ready to be read through select
		rList,wList,error_sockets = select.select(connected_list,[],[])

		for sock in rList:
			if sock == server_socket:
				# Handle the case in which there is a new connection recieved through server_socket
				sockfd, addr = server_socket.accept()
				name=sockfd.recv(buffer).decode()
				connected_list.append(sockfd)
				record[addr]=""
				print("record and conn list ",record,connected_list)

				existing_user = False
				conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="Ameya563")
				cur = conn.cursor()
				cur.execute(f"SELECT * FROM USERS WHERE username = '{name}'")
				for i in cur.fetchall():
					print("found in db: ", i)
					if(i[1]==name):
						existing_user=True
				cur.close()
				conn.close()

				if(existing_user):
					validated[addr]=0
					print("Client (%s, %s) attempting login" % addr," [",record[addr],"]")
					sockfd.send("\33[32m\r\33[1m Welcome back! Password: \n\33[0m".encode())
					record[addr] = name
				else:
					validated[addr]=-1
					print("New client (%s, %s) registering" % addr," [",record[addr],"]")
					sockfd.send("\33[32m\r\33[1m Welcome to chat room! Please create a password: \n\33[0m".encode())
					record[addr] = name

			#Some incoming message from a client
			else:
				# Data from client
				try:
					data1 = sock.recv(buffer).decode()
					#get addr of client sending the message
					i,p=sock.getpeername()
					if validated[(i,p)]==6:
						arr = data1.split("-", 1)
						receiver = arr[0].strip()
						#print "sock is: ",sock
						data=(arr[1][:arr[1].index("\n")]).strip()	
						#print "\ndata received: ",data
						print(receiver)
						if data == "tata":
							msg="\r\33[1m"+"\33[31m "+record[(i,p)]+" left the conversation \33[0m\n"
							send_to_all(sock,msg)
							print("Client (%s, %s) is offline" % (i,p)," [",record[(i,p)],"]")
							del record[(i,p)]
							connected_list.remove(sock)
							sock.close()
							continue
						else:
							msg= record[(i,p)] + ": " + data + "\n"
							if(receiver == "all"):
								send_to_all(sock,msg)
							else:
								send_to_one(sock, "Personal Message- " + msg, receiver)
					
					elif validated[(i,p)]==-1:#incoming data is password of a new user
						add_new_user(sock, i, p, data1)
					elif validated[(i,p)] in [0,1,2]:#incoming data is password of an existing user
						authenticate(sock, i, p, data1)

						
				#abrupt user exit
				except Exception as e:
					print(e)
					(i,p)=sock.getpeername()
					send_to_all(sock, "\r\33[31m \33[1m"+record[(i,p)]+" left the conversation unexpectedly\33[0m\n")
					print("Client (%s, %s) is offline (error)" % (i,p)," [",record[(i,p)],"]\n")
					del record[(i,p)]
					connected_list.remove(sock)
					sock.close()
					continue

	server_socket.close()