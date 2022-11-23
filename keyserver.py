import socket
import select
import psycopg2
from constants import *
from utilities import *
import crypto
from base64 import b64encode


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
            print("DEBUG: Accepted connection")
            data = from_recv(sockfd.recv(4096))
            print(f"DEBUG: Recevied data {data}")
            if "command" in data:
                conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname="fastchatdb", user="postgres", password="AshwinPostgre")
                cur = conn.cursor()
                command = data["command"]

                if command == "STORE":
                    username = data["username"]
                    key = data["key"]
                    type = data["type"]
                    if(type=="group"):
                        cur.execute(f"DELETE FROM KEYSERVER WHERE username='{username}'")
                        cur.execute(f"INSERT INTO KEYSERVER VALUES ('{username}', '{key}', '{type}')")
                        conn.commit()
                        print("[DEBUG]: Successfully stored")
                        sockfd.send(to_send({"command": "INFO", "msg": "Successfully stored!\n"}))            
                    else:
                        cur.execute(f"SELECT * FROM KEYSERVER WHERE username='{username}' AND type='{type}'")
                        if(len(cur.fetchall()) > 0):
                            print("[DEBUG]: Error: User already exists")
                            sockfd.send(to_send({"command": "ERROR", "msg": "User already exists!\n"}))
                        else:
                            cur.execute(f"INSERT INTO KEYSERVER VALUES ('{username}', '{key}', '{type}')")
                            conn.commit()
                            print("[DEBUG]: Successfully stored")
                            sockfd.send(to_send({"command": "INFO", "msg": "Successfully stored!\n"}))
                    
                elif command == "RETRIEVE":
                    username = data["username"]
                    type = data["type"]
                    cur.execute(f"SELECT * FROM KEYSERVER WHERE username='{username}' AND type='{type}'")
                    records = cur.fetchall()
                    if len(records) == 0:
                        print("[DEBUG] Error: User not found")
                        sockfd.send(to_send({"command": "ERROR", "msg": "User not found\n"}))
                    else:
                        print(f"[DEBUG] Sent public key to {sockfd.getpeername()}")
                        ks_privkey = crypto.import_key("KEYSERVER_PRIVKEY.pem")
                        sockfd.send(to_send({"command": "PUBKEY", "pubkey": records[0][1], "signature": b64encode(crypto.sign(ks_privkey, records[0][1].encode())).decode()}))
                else:
                    sockfd.send(to_send({"command": "ERROR", "msg": "Command not recognised!\n"}))
                cur.close()
                conn.close()
            else:
                sockfd.send(to_send({"command": "ERROR", "msg": "Protocol not followed!\n"}))
            
            sockfd.close()