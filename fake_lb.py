import socket, select
import random
from utilities import *


def gen_auth_token():
    token = random.randint(10000, 20000)
    log("Generated authentication token!")
    return token

def round_robin():
	global round_robin_index
	round_robin_index = (round_robin_index%5)+1
	return round_robin_index


def num_of_clients():
    return num_clients_list.index(min(num_clients_list))+1


def hash_port(port):
	return port % NUM_SERVERS


def get_server_recommendation(choice):
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
    port_servers[5000+ (server-5000)*100].send(to_send({'command':'authentication token', 'token':token}))
    log("Sent authentication token to server!")
    
    new_conn_socket.send(to_send({'command':'authentication token', 'server port':server, 'token':token}))
    log("Sent server recommendation and authentication token to client!")


def handle_pinging_socket(sock):
    pinging_socket_number = (sock.getpeername()[1]-5000)//100
    pinging_socket_data = from_recv(sock.recv(1024))
    if pinging_socket_data["type"] == 'increase':
        num_clients_list[pinging_socket_number-1] +=1
        log(f"Number of clients connected to {pinging_socket_number} incremented!")
    else:
        num_clients_list[pinging_socket_number-1] -=1
        log(f"Number of clients connected to {pinging_socket_number} decremented!")


if __name__ == "__main__":
    logfd = open("logs/servers_logs/load_balancer.log", 'w')
    def log(msg):
        log_to_file(msg, logfd)

    log("Load Balancer online!")

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

