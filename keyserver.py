import socket
import select
import psycopg2


connected_list = []
port = 5013

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind(("localhost", port))
server_socket.listen(10)

while True:
    rList, wList, eList = select.select([server_socket], [], [])

    for sock in rList:
        if sock == server_socket:
            print("DEBUG: Incoming connection to server socket!")
            sockfd, addr = server_socket.accept()
            data = sockfd.recv(4096).decode()
            print(f"DEBUG: Recevied data {data}")
            if ':' in data:
                conn = psycopg2.connect(host="localhost", port="5432", dbname="fastchatdb", user="postgres", password="AshwinPostgre")
                cur = conn.cursor()
                command = data.split(':')[0]
                if command == "STORE":
                    username = data.split(':')[1]
                    key = data.split(':')[2]
                    cur.execute(f"SELECT * FROM KEYSERVER WHERE username='{username}'")
                    if(len(cur.fetchall()) > 0):
                        sockfd.send("ERROR:User already exists!\n".encode())
                    else:
                        cur.execute(f"INSERT INTO KEYSERVER VALUES ('{username}', '{key}')")
                        conn.commit()
                        sockfd.send("INFO:Successfully stored!\n".encode())
                elif command == "RETRIEVE":
                    username = data.split(':')[1]
                    cur.execute(f"SELECT * FROM KEYSERVER WHERE username='{username}'")
                    records = cur.fetchall()
                    if len(records) == 0:
                        sockfd.send("User Not Found\n".encode())
                    else:
                        sockfd.send(records[0][1].encode())
                else:
                    sockfd.send("ERROR:No, why? Just why?\n".encode())
                cur.close()
                conn.close()
            else:
                sockfd.send("ERROR:What? Why? Where? No!\n".encode())
            
            sockfd.close()