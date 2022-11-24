import socket
import select
import psycopg2
from constants import *
from utilities import *
import crypto
from base64 import b64encode

def handle_storage(conn, cur, data):
    username = data["username"]
    key = data["key"]
    type = data["type"]
    log(f"Attempting to store public key of {username}")
    if(type=="group"):
        cur.execute(f"DELETE FROM KEYSERVER WHERE username='{username}'")
        cur.execute(f"INSERT INTO KEYSERVER VALUES ('{username}', '{key}', '{type}')")
        conn.commit()
        print("[DEBUG]: Successfully stored")
        log("Successfully stored!")
        sockfd.send(to_send({"command": "INFO", "msg": "Successfully stored!\n"}))            
    else:
        cur.execute(f"SELECT * FROM KEYSERVER WHERE username='{username}' AND type='{type}'")
        if(len(cur.fetchall()) > 0):
            print("[DEBUG]: Error: User already exists")
            log("User already exists!")
            sockfd.send(to_send({"command": "ERROR", "msg": "User already exists!\n"}))
        else:
            cur.execute(f"INSERT INTO KEYSERVER VALUES ('{username}', '{key}', '{type}')")
            conn.commit()
            print("[DEBUG]: Successfully stored")
            log("Successfully stored!")
            sockfd.send(to_send({"command": "INFO", "msg": "Successfully stored!\n"}))


def handle_retrieve(cur, data):
    username = data["username"]
    type = data["type"]
    log(f"Attempting to retrieve public key of {username}")
    cur.execute(f"SELECT * FROM KEYSERVER WHERE username='{username}' AND type='{type}'")
    records = cur.fetchall()
    if len(records) == 0:
        log("Error: User not found!")
        print("[DEBUG] Error: User not found")
        sockfd.send(to_send({"command": "ERROR", "msg": "User not found\n"}))
    else:
        log(f"Sent public key to {sockfd.getpeername()}")
        print(f"[DEBUG] Sent public key to {sockfd.getpeername()}")
        ks_privkey = crypto.import_key("KEYSERVER_PRIVKEY.pem")
        sockfd.send(to_send({"command": "PUBKEY", "pubkey": records[0][1], "signature": b64encode(crypto.sign(ks_privkey, records[0][1].encode())).decode()}))



def handle_response(data):
    if "command" in data:
        conn = psycopg2.connect(host="localhost", port=DATABASE_PORT, dbname=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD)
        cur = conn.cursor()
        log("Connected to database!")
        command = data["command"]

        if command == "STORE":
            handle_storage(conn, cur, data)  
        elif command == "RETRIEVE":
            handle_retrieve(cur, data)
        else:
            log("Error: Command not recognised!")
            sockfd.send(to_send({"command": "ERROR", "msg": "Command not recognised!\n"}))
        cur.close()
        conn.close()
    else:
        log("Error: Protocol not followed!")
        sockfd.send(to_send({"command": "ERROR", "msg": "Protocol not followed!\n"}))
    
    sockfd.close()
    log("Connection closed!")



if __name__ == "__main__":
    connected_list = []
    port = KEYSERVER_PORT

    logfd = open("keyserver.log", 'w')
    def log(msg):
        log_to_file(msg, logfd)

    log("Keyserver online!")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind(("localhost", port))
    server_socket.listen(10)

    while True:
        rList, wList, eList = select.select([server_socket], [], [])

        for sock in rList:
            if sock == server_socket:
                print("DEBUG: Incoming connection to server socket!")
                log("Incoming connection to server socket!")
                sockfd, addr = server_socket.accept()
                print("DEBUG: Accepted connection")
                log("Connection accepted!")
                data = from_recv(sockfd.recv(4096))
                print(f"DEBUG: Recevied data {data}")
                log(f"Received response!")
                handle_response(data)