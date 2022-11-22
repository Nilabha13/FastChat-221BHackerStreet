import socket, select, sys
from constants import *
from utilities import *
import crypto
import os.path

# LOAD_BALANCER_PORT = 5000

def display_pending_messages(messages):
    print(f"You have {len(messages)} pending messages!")
    for msg in messages:
        if(msg["type"]=="image"):
            list_of_images.append(msg)
        else:
            list_of_messages.append(msg)

def print_menu():
    print("\nEnter Command No.:\n1) RECEIVE MESSAGES\n2) RECEIVE IMAGES\n3) SEND MESSAGE\n4) SEND IMAGE\n5) QUIT\n")

def encryptData(data, to_username, is_image=False):
    if not is_image:
        data = data.encode()
    ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ks.connect(('localhost', KEYSERVER_PORT))
    ks.send(to_send({"command": "RETRIEVE", "username": to_username}))
    ks_response = from_recv(ks.recv(4096))
    if ks_response["command"] == "PUBKEY":
        print("Inside")
        to_user_pubkey = crypto.str_to_key(ks_response["pubkey"])
        signature = b64decode(ks_response["signature"].encode())
        ks_pubkey = crypto.import_key("KEYSERVER_PUBKEY.pem")
        print("Let's go")
        if not crypto.verify_signature(ks_pubkey, ks_response['pubkey'].encode(), signature):
            print("Hi! It's me!")
            fp(signature)
            fp(crypto.decryptRSA(ks_pubkey, signature))
            fp(crypto.sha256(ks_response['pubkey'].encode()).digest())
            raise "Malicious tampering with keyserver!"
        print("Successfully returning...")
        return b64encode(crypto.encryptRSA(to_user_pubkey, data)).decode()
    else:
        print("[ERROR] Key server returned an error!")

def decryptData(data, self_username, is_image=False):
    privkey = crypto.import_key(f"mykeys/{self_username}_priv_key.pem")
    plaintext = crypto.decryptRSA(privkey, b64decode(data.encode()))
    if not is_image:
        plaintext = plaintext.decode()
    return plaintext

username = input("Enter a username: ")
initial = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
initial.connect(('localhost', LOAD_BALANCER_PORT))
lb_response = from_recv(initial.recv(1024))
token = lb_response["token"]
server_port = lb_response["server port"]
#fp(token)
#fp(server_port)
server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_connection.connect(('localhost', server_port))
print(username)
server_connection.send(to_send({"command": "first connection", "authentication token": token, "username": username}))
list_of_messages = []
list_of_images = []
while True:
    rlist, wlist, elist = select.select([server_connection, sys.stdin], [], [])
    for s in rlist:
        if s == server_connection:
            # data = s.recv(4096)
            # if not data:
            #     print('\33[31m\33[1m \rDISCONNECTED!!\n \33[0m')
            #     sys.exit()
            # elif "Welcome" in data.decode():
            #     print(data.decode())
            # else:
            #     list_of_messages.append(data.decode())
            data = s.recv(4096)
            if not data:
                print('\33[31m\33[1m \rDISCONNECTED!!\n \33[0m')
                sys.exit()
            response = from_recv(data)
            command = response["command"]
            if command == "new user":
                print("Welcome to FastChat - the application which lets you chat faster than the speed of light!")
                print("You are a new user!")
                password = input("Please enter a password: ")
                server_connection.send(to_send({"command": "new password", "password": password}))
                print(f"SENT to {server_connection.getpeername()}")
            elif command == "existing user":
                print("Welcome to FastChat - the application which lets you chat faster than the speed of light!")
                print("You are an existing user!")
                password = input("Please enter your password: ")
                server_connection.send(to_send({"command": "password authenticate", "password": password}))
                print(f"SENT to {server_connection.getpeername()}")
            elif command == "re-enter":
                print("The password you entered is incorrect!")
                password = input("Please enter your password: ")
                server_connection.send(to_send({"command": "password authenticate", "password": password}))
                print(f"SENT to {server_connection.getpeername()}")
            elif command == "register for keyServer":
                ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ks.connect(('localhost', KEYSERVER_PORT))
                pub_key, priv_key = crypto.gen_RSA_keys()
                crypto.export_key(pub_key, f"mykeys/{username}_pub_key.pem")
                crypto.export_key(priv_key, f"mykeys/{username}_priv_key.pem")
                ks.send(to_send({"command": "STORE", "username": username, "key": crypto.key_to_str(pub_key)}))
                print(f"SENT to KEYSERVER")
                print_menu()
            elif command == "pending messages":
                print("Password Authenticated!")
                messages = response["messages"]
                display_pending_messages(messages)
                print_menu()
            elif command == "user-user message":
                if response["type"] == "message":
                    list_of_messages.append(response)
                elif response["type"] == "image":
                    list_of_images.append(response)
        else:
            # message = sys.stdin.readline()
            # if(message.split("-", 1)[0].strip() == "read"):
            #     while len(list_of_messages) > 0:
            #         print(list_of_messages.pop(0))
            #     sys.stdout.flush()
            # else:
            #     server_connection.send(message.encode())
            #     sys.stdout.flush()
            command  = sys.stdin.readline().strip()
            if command == '1':
                # from_user = input("Enter username whose messages you want to read: ")
                print(f"You have {len(list_of_messages)} unread messages!")
                while len(list_of_messages) > 0:
                    message = list_of_messages.pop(0)
                    print(f'{message["sender username"]}: {decryptData(message["encrypted message"], username)}')
            elif command == '2':
                print(f"Downloading {len(list_of_images)} images!")
                while len(list_of_images) > 0:
                    image = list_of_images.pop(0)
                    filename = decryptData(image["filename"], username)
                    file = open("images/"+filename, 'wb')
                    file.write(decryptData(image["encrypted message"], username, True))
                    file.close()
                    # b64_to_img(image["encrypted message"], "images/"+image["filename"])
                    print(f'{image["sender username"]}: Downloaded {filename}')
            elif command == '3':
                to_username = input("Enter to username: ")
                message = input("Enter message: ")
                try:
                    print("Trying")
                    encrypted_message = encryptData(message, to_username)
                    print("Encryption successful!")
                    server_connection.send(to_send({"command": "user-user message","type": "message", "encrypted message": encrypted_message, "receiver username": to_username, "sender username": username}))
                except Exception as e:
                    print(e)
                    print("[WARNING] Connection to keyserver compromised! Not sending!")
            elif command == '4':
                to_username = input("Enter to username: ")
                filename = input("Enter filename: ")
                try:
                    file = open(filename, 'rb')
                    image = file.read()
                    file.close()
                    try:
                        server_connection.send(to_send({"command": "user-user message", "type": "image", "filename": encryptData(os.path.basename(filename), to_username), "encrypted message": encryptData(image, to_username, True), "receiver username": to_username, "sender username": username}))
                    except:
                        print("[WARNING] Connection to keyserver compromised! Not sending!")
                except:
                    print(f"[ERROR] {filename} does not exist!")
            elif command == '5':
                server_connection.close()
            else:
                print("Invalid command!")
            print_menu()