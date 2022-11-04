import socket, select
import random
NUM_SERVERS = 5
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('localhost', 5000))
s.listen(10)
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
        else:
            #handle client
            #load balancing comes here
            token = random.randint(10000, 20000)
            l = [5001, 5002, 5003, 5004, 5005]
            server = random.choice(l)
            new_conn_socket.send(f"{token} - {server}".encode())
            port_servers[5000 + 100 * (server - 5000)].send(str(token).encode())
            new_conn_socket.close()

            

