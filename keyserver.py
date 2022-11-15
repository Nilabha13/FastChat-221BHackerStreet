import socket
import select
import psycopg2
from constants import *
from utilities import *


connected_list = []
port = KEYSERVER_PORT

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind(("localhost", port))
server_socket.listen(10)

while True:
    rList, wList, eList = select.select([server_socket], [], [])

    for sock in rList:
        if sock == server_socket:
            print("DEBUG: Incoming connection to server socket!")
            sockfd, addr = server_socket.accept()
            data = from_recv(sockfd.recv(4096))
            print(f"DEBUG: Recevied data {data}")
            if "command" in data:
                conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname="fastchatdb", user="postgres", password="AshwinPostgre")
                cur = conn.cursor()
                command = data["command"]
                if command == "STORE":
                    username = data["username"]
                    key = data["key"]
                    cur.execute(f"SELECT * FROM KEYSERVER WHERE username='{username}'")
                    if(len(cur.fetchall()) > 0):
                        sockfd.send(to_send({"command": "ERROR", "msg": "User already exists!\n"}))
                    else:
                        cur.execute(f"INSERT INTO KEYSERVER VALUES ('{username}', '{key}')")
                        conn.commit()
                        sockfd.send(to_send({"command": "INFO", "msg": "Successfully stored!\n"}))
                elif command == "RETRIEVE":
                    username = data["username"]
                    cur.execute(f"SELECT * FROM KEYSERVER WHERE username='{username}'")
                    records = cur.fetchall()
                    if len(records) == 0:
                        sockfd.send(to_send({"command": "ERROR", "msg": "User not found\n"}))
                    else:
                        sockfd.send(to_send({"command": "PUBKEY", "pubkey": records[0][1].encode()}))
                else:
                    sockfd.send(to_send({"command": "ERROR", "msg": "Command not recognised!\n"}))
                cur.close()
                conn.close()
            else:
                sockfd.send(to_send({"command": "ERROR", "msg": "Protocol not followed!\n"}))
            
            sockfd.close()