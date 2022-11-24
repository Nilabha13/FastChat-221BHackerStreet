import socket, select
import random
from utilities import *

logfd = open("logs/servers_logs/load_balancer.log", 'w')
def log(msg):
    log_to_file(msg, logfd)

log("Load Balancer online!")

round_robin_index = 1

def round_robin():
	global round_robin_index
	round_robin_index = (round_robin_index%5)+1
	return round_robin_index

def num_of_clients():
    return num_clients_list.index(min(num_clients_list))+1

def hash_port(port):
	return port%5

# def response_time():
# 	global connected_list
# 	for i in connected_list:
# 		i.send("ping".encode())

def message_freq():
	return 1



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
                #new_conn_socket.send("Hello from LB".encode())
                # fp(addr)
            else:
                log(f"Connection from client ({new_conn_socket.getpeername()}) accepted!")
                #handle client
                #load balancing comes here
                token = random.randint(10000, 20000)
                log("Generated authentication token!")

                if(choice=="round robin"):
                    server_number = round_robin()
                    server = 5000 + server_number

                
                if(choice=="number of clients"):
                    server_number = num_of_clients()
                    server = 5000 + server_number

                
                if(choice=="hash port"):
                    server_number = hash_port(addr[1])
                    server = 5000 + server_number

                log(f"Recommending server {server}")
                
                l = [5001, 5002, 5003, 5004, 5005]
                port_servers[5000+ (server-5000)*100].send(to_send({'command':'authentication token', 'token':token}))
                log("Sent authentication token to server!")
                
                new_conn_socket.send(to_send({'command':'authentication token', 'server port':server, 'token':token}))
                log("Sent server recommendation and authentication token to client!")
                # fp(server)

                new_conn_socket.close()
                log("Connection closed!")
        else:
            pinging_socket_number = (sock.getpeername()[1]-5000)//100
            pinging_socket_data = from_recv(sock.recv(1024))
            if pinging_socket_data["type"] == 'increase':
                num_clients_list[pinging_socket_number-1] +=1
                log(f"Number of clients connected to {pinging_socket_number} incremented!")
            else:
                num_clients_list[pinging_socket_number-1] -=1
                log(f"Number of clients connected to {pinging_socket_number} decremented!")



            

