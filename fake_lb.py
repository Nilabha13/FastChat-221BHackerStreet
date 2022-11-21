import socket, select
import random
import psycopg2
from utilities import *


round_robin_index = 1

def round_robin():
	global round_robin_index
	round_robin_index = (round_robin_index%5)+1
	return round_robin_index

def num_of_clients():
	conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
	cur = conn.cursor()
	cur.execute("""SELECT count(*), current_server_number FROM USERS GROUP BY current_server_number""")
	m_clients = 0
	for i in cur.fetchall():
		if i[0]<=m_clients:
			m_clients=i[0]
			m_server_name = i[1]+5000
	cur.close()
	conn.close()
	return((m_server_name-5000)/100)

def hash_port(port):
	return port%5

# def response_time():
# 	global connected_list
# 	for i in connected_list:
# 		i.send("ping".encode())

def message_freq():
	return 1





NUM_SERVERS = 5
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('localhost', 5000))
s.listen(10)

choice = "round_robin"

port_servers = {}
valid_server_ports = []

for i in range(1, NUM_SERVERS + 1):
    valid_server_ports.append(5000 + i * 100)

while True:
    rlist, wlist, elist = select.select([s], [], [])
    if s in rlist:
        new_conn_socket, addr = s.accept()
        if addr[1] in valid_server_ports:
            port_servers[addr[1]] = new_conn_socket
            #new_conn_socket.send("Hello from LB".encode())
            # fp(addr)
        else:
            #handle client
            #load balancing comes here
            token = random.randint(10000, 20000)

            if(choice=="round_robin"):
                server_number = round_robin()
                server = 5000 + server_number

            
            if(choice=="number of clients"):
                server_number = num_of_clients()
                server = 5000 + server_number

            
            if(choice=="hash port"):
                server_number = hash_port(addr[1])
                server = 5000 + server_number
            
            l = [5001, 5002, 5003, 5004, 5005]
            new_conn_socket.send(to_send({'command':'authentication token', 'server port':server, 'token':token}))
            # fp(server)
            port_servers[5000+ (server-5000)*100].send(to_send({'command':'authentication token', 'token':token}))
            new_conn_socket.close()

            

