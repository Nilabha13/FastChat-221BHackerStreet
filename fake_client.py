import socket, select, sys
from constants import *
from utilities import *
import crypto
import os.path
import os
import re
# LOAD_BALANCER_PORT = 5000

def display_pending_messages(messages):
    print(f"You have {len(messages)} pending messages!")
    for msg in messages:
        if(msg["type"]=="image"):
            list_of_images.append(msg)
        else:
            list_of_messages.append(msg)

def print_menu():
    print("\nEnter Command No.:\n1) RECEIVE MESSAGES\n2) RECEIVE IMAGES\n3) SEND MESSAGE\n4) SEND IMAGE\n5) SEND GROUP MESSAGE\n6) SEND GROUP IMAGE\n7) CREATE GROUP\n8) MANAGE MY GROUPS\n9) QUIT\n")

def encryptData(data, to_username, is_image=False, type = 'fastchatter'):
    global prev_users
    if not is_image:
        data = data.encode()
    if to_username not in prev_users:
        ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ks.connect(('localhost', KEYSERVER_PORT))
        ks.send(to_send({"command": "RETRIEVE", "username": to_username, 'type':type}))
        ks_response = from_recv(ks.recv(4096))
        if ks_response["command"] == "PUBKEY":
            print("Inside")
            to_user_pubkey = crypto.str_to_key(ks_response["pubkey"])
            signature = b64decode(ks_response["signature"].encode())
            ks_pubkey = crypto.import_key("KEYSERVER_PUBKEY.pem")
            print("Let's go")
            if not crypto.verify_signature(ks_pubkey, ks_response['pubkey'].encode(), signature):
                print("Hi! It's me!")
                # fp(signature)
                # fp(crypto.decryptRSA(ks_pubkey, signature))
                # fp(crypto.sha256(ks_response['pubkey'].encode()).digest())
                raise "Malicious tampering with keyserver!"
            print("Successfully returning...")
            crypto.export_key(to_user_pubkey, f"mykeys/{username}_{to_username}_pub_key.pem")
            prev_users.append(to_username)
            return b64encode(crypto.encryptRSA(to_user_pubkey, data)).decode()
        else:
            print("[ERROR] Key server returned an error!")
    else:
        to_user_pubkey = crypto.import_key(f"mykeys/{username}_{to_username}_pub_key.pem")
        return b64encode(crypto.encryptRSA(to_user_pubkey, data)).decode()

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
prev_users = []
r = re.compile(f"({username}_)(.*)(_pub_key.pem)")
for i in os.listdir("mykeys"):
    match = re.search(r, i)
    if match != None:
        prev_users.append(match.group(2))
        
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
                print('\n\33[31m\33[1m \rDISCONNECTED!!\n \33[0m')
                sys.exit()
            response = from_recv(data)
            command = response["command"]
            if command == "new user":
                print("Welcome to FastChat - the application which lets you chat faster than the speed of light!")
                print("You are a new user!")
                password = input("Please enter a password: ")
                # server_connection.send(to_send({"command": "new password", "password": password}))
                # print(f"SENT to {server_connection.getpeername()}")
                servers_pubkey = crypto.import_key("SERVERS_PUBKEY.pem")
                print("[DEBUG] RETRIEVED servers' public key")
                password_enc = b64encode(crypto.encryptRSA(servers_pubkey, password.encode())).decode()
                server_connection.send(to_send({"command": "new password", "encrypted password": password_enc}))
                print(f"SENT to {server_connection.getpeername()}")
            elif command == "existing user" or command == "re-enter":
                if command == "existing user":
                    print("Welcome to FastChat - the application which lets you chat faster than the speed of light!")
                    print("You are an existing user!")
                else:
                    print("The password you entered is incorrect!")
                password = input("Please enter your password: ")
                # server_connection.send(to_send({"command": "password authenticate", "password": password}))
                # print(f"SENT to {server_connection.getpeername()}")
                server_connection.send(to_send({"command": "password authenticate lvl1", "username": username}))
                response = from_recv(server_connection.recv(4096))
                assert response["command"] == "password authenticate lvl2"
                fp(response["aes_key"])
                aes_key = decryptData(response["aes_key"], username, True)
                aes_iv = decryptData(response["aes_iv"], username, True)
                print("[DEBUG] RECEIVED aes_key & aes_iv")
                server_connection.send(to_send({"command": "password authenticate lvl3", "username": username, "encrypted password": b64encode(crypto.encryptAES(aes_key, aes_iv, password.encode())).decode()}))
            # elif command == "re-enter":
            #     print("The password you entered is incorrect!")
            #     password = input("Please enter your password: ")
            #     server_connection.send(to_send({"command": "password authenticate", "password": password}))
            #     print(f"SENT to {server_connection.getpeername()}")
            elif command == "register for keyServer":
                print("[DEBUG] Registering to KeyServer")
                ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ks.connect(('localhost', KEYSERVER_PORT))
                pub_key, priv_key = crypto.gen_RSA_keys()
                crypto.export_key(pub_key, f"mykeys/{username}_pub_key.pem")
                crypto.export_key(priv_key, f"mykeys/{username}_priv_key.pem")
                ks.send(to_send({"command": "STORE", "username": username, "key": crypto.key_to_str(pub_key), 'type':'fastchatter'}))
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

            command  = sys.stdin.readline().strip()
            if command == '1':
                # from_user = input("Enter username whose messages you want to read: ")
                print(f"You have {len(list_of_messages)} unread messages!")
                while len(list_of_messages) > 0:
                    message = list_of_messages.pop(0)
                    print(message)
                    if(message['class']=='group invite'):
                        grp_priv_key = crypto.str_to_key(decryptData(message["encrypted message"], username))
                        groupname = message["group name"]
                        crypto.export_key(grp_priv_key, f"mykeys/{username}_{groupname}_priv_key.pem")

                        ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        ks.connect(('localhost', KEYSERVER_PORT))
                        ks.send(to_send({"command": "RETRIEVE", "username": groupname, 'type':'group'}))
                        ks_response = from_recv(ks.recv(4096))
                        if(ks_response["command"] == "PUBKEY"):
                            to_user_pubkey = crypto.str_to_key(ks_response["pubkey"])

                            crypto.export_key(to_user_pubkey, f"mykeys/{username}_{groupname}_pub_key.pem")
                            if(groupname in prev_users):
                                prev_users.remove(groupname)
                            prev_users.append(groupname)
                        else:
                            print("[ERROR] Key server returned an error!")
                    
                    elif message['class']=='user message':
                        print(f'{message["sender username"]}: {decryptData(message["encrypted message"], username)}')
                    
                    elif message['class']=='group message':
                        groupname = message['group name']
                        print(f'{groupname}:{message["sender username"]}: {decryptData(message["encrypted message"], username+"_"+groupname)}')
                        print("group message here")
                    
            elif command == '2':
                print(f"Downloading {len(list_of_images)} images!")
                while len(list_of_images) > 0:
                    image = list_of_images.pop(0)
                    if(image['class']=='group message'):
                        groupname = image["group name"]
                        filename = decryptData(image["filename"], username+"_"+groupname)
                        file = open("images/"+filename, 'wb')
                        file.write(decryptData(image["encrypted message"], username+"_"+groupname, True))
                        file.close()
                        print(f'{image["group name"]}:{image["sender username"]}: Downloaded {filename}')

                    elif(image['class']=='user message'):
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
                    server_connection.send(to_send({"command": "user-user message","type": "message", "encrypted message": encrypted_message, "receiver username": to_username, "sender username": username, "class":"user message"}))
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
                to_groupname = input("Enter to groupname: ")
                message = input("Enter message: ")
                try:
                    print("Trying")
                    encrypted_message = encryptData(message, to_groupname, type="group")
                    print("Encryption successful!")
                    server_connection.send(to_send({"command": "user-user message","type": "message", "encrypted message": encrypted_message, "receiver username": '', "sender username": username, "class":"group message", "group name": to_groupname}))
                    response = from_recv(server_connection.recv(4096))
                    if(response["command"]) == "error, bad member":
                        print("You are not a member of this group")
                except Exception as e:
                    print(e)
                    print("[WARNING] Connection to keyserver compromised! Not sending!")

            elif command == '6':
                to_groupname = input("Enter to groupname: ")
                filename = input("Enter filename: ")
                try:
                    file = open(filename, 'rb')
                    image = file.read()
                    file.close()
                    try:
                        server_connection.send(to_send({"command": "user-user message", "type": "image", "filename": encryptData(os.path.basename(filename), to_groupname, type='group'), "encrypted message": encryptData(image, to_groupname, True, type='group'), "receiver username": "", "sender username": username, "class":"group message" ,"group name":to_groupname}))
                    except Exception as e:
                        print(e)
                        print("[WARNING] Connection to keyserver compromised! Not sending!")
                except:
                    print(f"[ERROR] {filename} does not exist!")

            elif command == '7':
                #wish to create group
                groupname = input("Enter groupname: ")
                num_of_members = input("Enter number of members: ")
                members = list(eval(input("Enter comma separated list of members(there should be quotes around each name): ")))
                print("[DEBUG] received: ", members)

                ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ks.connect(('localhost', KEYSERVER_PORT))
                pub_key, priv_key = crypto.gen_RSA_keys()
                crypto.export_key(pub_key, f"mykeys/{username}_{groupname}_pub_key.pem")
                crypto.export_key(priv_key, f"mykeys/{username}_{groupname}_priv_key.pem")
                ks.send(to_send({"command": "STORE", "username": groupname, "key": crypto.key_to_str(pub_key), 'type':'group'}))
                print(f"SENT to KEYSERVER")


                server_connection.send(to_send({"command":"create group", "group name":groupname, "admin":username, "member list":members+[username]}))
                print("[DEBUG] sent group creation request to servers")

                for member in members:
                    encrypted_key = encryptData(crypto.key_to_str(priv_key), member)
                    server_connection.send(to_send({'command':'user-user message', 'encrypted message':encrypted_key, 'receiver username':member, 'sender username':username, 'type':'message', 'class':'group invite', 'group name':groupname}))
                    print('[DEBUG] sent private key for group to member: ', member)
                


            elif command == '8':
                groupname = input("Enter groupname: ")
                add_choice = input("Would you like to add or remove members? (enter 1 for add and 2 for remove)")
                if(add_choice=='1'):
                    num_of_members = input("Enter number of members: ")
                    members = list(eval(input("Enter comma separated list of members: ")))
                    server_connection.send(to_send({"command":"add to group", "group name":groupname, "member list":members}))

                    response = from_recv(server_connection.recv(4096))
                    if(response["command"]=="error, bad admin"):
                        print("You are not admin for this group!")
                        continue
                
                    priv_key = crypto.import_key(f"mykeys/{username}_{groupname}_priv_key.pem")
                    for member in members:
                        encrypted_key = encryptData(crypto.key_to_str(priv_key), member)
                        server_connection.send(to_send({'command':'user-user message', 'encrypted message':encrypted_key, 'receiver username':member, 'sender username':username, 'type':'message', 'class':'group invite', 'group name':groupname}))                
                
                elif(add_choice=='2'):
                    members = list(eval(input("Enter comma separated list of members: "))) #will ignore any members entered but not in group
                    server_connection.send(to_send({"command":"remove from group", "group name":groupname, "member list":members}))
                    response = from_recv(server_connection.recv(4096))
                    if(response["command"]=="error, bad admin"):
                        print("You are not admin for this group!")
                        continue

                    members = response["members"]

                    ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    ks.connect(('localhost', KEYSERVER_PORT))
                    pub_key, priv_key = crypto.gen_RSA_keys()
                    crypto.export_key(pub_key, f"mykeys/{username}_{groupname}_pub_key.pem")
                    crypto.export_key(priv_key, f"mykeys/{username}_{groupname}_priv_key.pem")
                    ks.send(to_send({"command": "STORE", "username": groupname, "key": crypto.key_to_str(pub_key), 'type':'group'}))
                    print(f"SENT to KEYSERVER")
            
                    for member in members:
                        encrypted_key = encryptData(crypto.key_to_str(priv_key), member)
                        server_connection.send(to_send({'command':'user-user message', 'encrypted message':encrypted_key, 'receiver username':member, 'sender username':username, 'type':'message', 'class':'group invite', 'group name':groupname}))
                        print('[DEBUG] sent private key for group to member: ', member)
                    
                else:
                    print('invalid choice')
                    continue



            elif command == '9':
                server_connection.close()
            else:
                print("Invalid command!")
            print_menu()