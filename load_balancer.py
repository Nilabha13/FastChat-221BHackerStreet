import socket, select
import random
from utilities import *



def gen_auth_token():
	"""
	Generates a random authentication token(int) which will be used for authentication when the client connects to the server. Returns the token

	:rtype: int
	"""
	token = random.randint(10000, 20000)
	log("Generated authentication token!")
	return token

def round_robin():
	"""
	This is one of the load balancing strategies. Round robin mantains a global variable corresponding to the last assigned server. 
	The next client will go to the next server in a cyclic manner. Returns the server number from the interval [1, 5]

	:rtype: int
	"""
	global round_robin_index
	round_robin_index = (round_robin_index%5)+1
	return round_robin_index


def num_of_clients():
	"""
	This is one of the load balancing strategies. Number of Clients mantains a global variable corresponding to the number of clients currently 
	connected to each of the servers. A new incoming client will go to the server with minimum connected clients. 
	Returns the server number from the interval [1, 5]

	:rtype: int
	"""
	return num_clients_list.index(min(num_clients_list))+1


def hash_port(port):
	"""
	This is one of the load balancing strategies. It takes the port of the client and hashes it mod 5. It assigns a server based on that.
	This strategy is similar to random load balancing, it is expected to assign approximately equal number of users across the servers.
	Returns the server number from the interval [1, 5]

	:param port: port number of client
	:type port: int
	:rtype: int
	"""
	return (port % NUM_SERVERS) + 1


def random_server():
	"""This is one of the load balancing strategies. It assigns a random server to the client.
	This strategy is resilient against most malicious attacks against load balancing strategies.
	Returns the server number from the interval [1, 5]

	:return: The assigned server number
	:rtype: int
	"""
	return random.randrange(1, NUM_SERVERS+1)


def get_server_recommendation(choice):
	"""
	This function returns the server recommendation based on the currently chosen load balancer strategy. It returns the port number of the server
	to which the client should connect from the interval [5001, 5005]

	:param choice: load balancing choice
	:type choice: string
	:rtype: int
	"""
	if(choice=="round robin"):
		server_number = round_robin()
		server = 5000 + server_number
	elif(choice=="number of clients"):
		server_number = num_of_clients()
		server = 5000 + server_number
	elif(choice=="hash port"):
		server_number = hash_port(addr[1])
		server = 5000 + server_number

	log(f"Recommending server {server}")
	return server


def send_auth_tokens(token, server):
	"""
	Once the authentication token and the server number have been generated, they are sent to the server and the client via this function.
	The function doesn't return anything

	:param token: contains token number that was generated
	:type token: int
	:param server: contains server number that was generated
	:type server: int
	"""
	port_servers[5000+ (server-5000)*100].send(to_send({'command':'authentication token', 'token':token}))
	log("Sent authentication token to server!")
	
	new_conn_socket.send(to_send({'command':'authentication token', 'server port':server, 'token':token}))
	log("Sent server recommendation and authentication token to client!")


def handle_pinging_socket(sock):
	"""
	This function is meant to handle a pinging server socket from the load balancer's end. The server socket is expected to be 
	sending back that a user has connected/disconnected from it. This is dealt with accordingly and the load balancer updates its local 
	variables. The function doesn't return anything.

	:param sock: contains token number that was generated
	:type sock: int
	"""
	pinging_socket_number = (sock.getpeername()[1]-5000)//100
	pinging_socket_data = from_recv(sock.recv(1024))
	if pinging_socket_data["type"] == 'increase':
		num_clients_list[pinging_socket_number-1] +=1
		log(f"Number of clients connected to {pinging_socket_number} incremented!")
	else:
		num_clients_list[pinging_socket_number-1] -=1
		log(f"Number of clients connected to {pinging_socket_number} decremented!")


if __name__ == "__main__":
	create_dirs_if_not_exist_recursive(["logs", "servers_logs"])
	logfd = open(os.path.join("logs", "servers_logs", "load_balancer.log"), 'w')
	def log(msg):
		log_to_file(msg, logfd)


	round_robin_index = 1

	num_clients_list = [0,0,0,0,0]

	NUM_SERVERS = 5
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(('localhost', 5000))
	s.listen(10)

	choice = "number of clients"

	log(f"Load balancing strategy: {choice}")

	port_servers = {}
	list_port_servers = []
	valid_server_ports = []

	for i in range(1, NUM_SERVERS + 1):
		valid_server_ports.append(5000 + i * 100)

	while True:
		rlist, wlist, elist = select.select([s]+list_port_servers, [], [])
		for sock in rlist:
			if sock == s:
				log("Incoming connection to server socket!")
				new_conn_socket, addr = s.accept()
				if addr[1] in valid_server_ports:
					log(f"Connection from server ({new_conn_socket.getpeername()}) accepted!")
					port_servers[addr[1]] = new_conn_socket
					list_port_servers.append(new_conn_socket)
				else:
					log(f"Connection from client ({new_conn_socket.getpeername()}) accepted!")

					token = gen_auth_token()
					server = get_server_recommendation(choice)
					send_auth_tokens(token, server)

					new_conn_socket.close()
					log("Connection closed!")
			else:
				handle_pinging_socket(sock)

