import socket, select, sys
from constants import *
from utilities import *
import crypto
import os.path
import os
import re
import time
# LOAD_BALANCER_PORT = 5000

def log(msg):
    log_to_file(msg, logfd)

def display_pending_messages(messages):
    print(f"You have {len(messages)} pending messages!")
    for msg in messages:
        if(msg["type"]=="image"):
            list_of_images.append(msg)
            log(f"received image from {msg['receiver username']}. Stored ")
        else:
            list_of_messages.append(msg)
            log(f"received message from {msg['receiver username']}. Stored ")


def print_message(message):
    if message['class'] == 'group invite':
        print(f"[{message['time_sent']}]\n You have been added to group {message['group name']} by admin {message['sender username']}")
        log(f"printed group invite comand")

    if message['class'] == 'group update':
        print(f"[{message['time_sent']}]\nGroup {message['group name']}'s info updated by admin {message['sender username']}")
        log(f"printed group updation comand")

    elif message['class']=='user message':
        print(f'[{message["time_sent"]}]\n{message["sender username"]}: {decryptData(message["encrypted message"], username)}')
        log(f"printed user message")

                    
    elif message['class']=='group message':
        groupname = message['group name']
        print(f'[{message["time_sent"]}]\nOn group {groupname} - {message["sender username"]}: {decryptData(message["encrypted message"], username+"_"+groupname)}')
        log(f"printed group message")


def print_menu():
    print("\nEnter Command No.:\n1) VIEW RECEIVED MESSAGES\n2) VIEW RECEIVED IMAGES\n3) SEND MESSAGE\n4) SEND IMAGE\n5) SEND GROUP MESSAGE\n6) SEND GROUP IMAGE\n7) CREATE GROUP\n8) MANAGE MY GROUPS\n9) QUIT\n")

def encryptData(data, to_username, is_image=False, type = 'fastchatter'):
    global prev_users
    if not is_image:
        data = data.encode()
    if to_username not in prev_users:
        log(f"contacting key server from client for public key of {to_username}")
        ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ks.connect(('localhost', KEYSERVER_PORT))
        ks.send(to_send({"command": "RETRIEVE", "username": to_username, 'type':type}))
        ks_response = from_recv(ks.recv(4096))
        if ks_response["command"] == "PUBKEY":
            # print("Inside")
            to_user_pubkey = crypto.str_to_key(ks_response["pubkey"])
            signature = b64decode(ks_response["signature"].encode())
            ks_pubkey = crypto.import_key("KEYSERVER_PUBKEY.pem")
            log(f"keyserver signature done")
            # print("Let's go")
            if not crypto.verify_signature(ks_pubkey, ks_response['pubkey'].encode(), signature):
                # print("Hi! It's me!")
                # fp(signature)
                # fp(crypto.decryptRSA(ks_pubkey, signature))
                # fp(crypto.sha256(ks_response['pubkey'].encode()).digest())
                log(f"Malicious tampering with keyserver!")
                raise "Malicious tampering with keyserver!"
            # print("Successfully returning...")
            crypto.export_key(to_user_pubkey, f"mykeys/{username}_{to_username}_pub_key.pem")
            prev_users.append(to_username)
            return b64encode(crypto.encryptRSA(to_user_pubkey, data)).decode()
        else:
            log("[ERROR] Key server returned an error!")
            print("[ERROR] Key server returned an error!")
    else:
        log(f"public key is available, need not contact keyserver")
        to_user_pubkey = crypto.import_key(f"mykeys/{username}_{to_username}_pub_key.pem")
        return b64encode(crypto.encryptRSA(to_user_pubkey, data)).decode()

def decryptData(data, self_username, is_image=False):
    log(f"decrypting data for {self_username}")
    privkey = crypto.import_key(f"mykeys/{self_username}_priv_key.pem")
    plaintext = crypto.decryptRSA(privkey, b64decode(data.encode()))
    if not is_image:
        plaintext = plaintext.decode()
    return plaintext

def handle_new_user(server_sock):
    log(f"recognised as new user")
    print("Welcome to FastChat - the application which lets you chat faster than the speed of light!")
    print("You are a new user!")
    password = input("Please enter a password: ")
    # server_connection.send(to_send({"command": "new password", "password": password}))
    # print(f"SENT to {server_connection.getpeername()}")
    servers_pubkey = crypto.import_key("SERVERS_PUBKEY.pem")
    # print("[DEBUG] RETRIEVED servers' public key")
    password_enc = b64encode(crypto.encryptRSA(servers_pubkey, password.encode())).decode()
    server_sock.send(to_send({"command": "new password", "encrypted password": password_enc}))
    log(f"password received from user, sent encrypted password to server")

def prompt_for_password(command):
    if command == "existing user":
        print("Welcome to FastChat - the application which lets you chat faster than the speed of light!")
        print("You are an existing user!")
        log(f"recognised as an existing user!")
    else:
        print("The password you entered is incorrect!")
        log(f"wrong password sent, RETRY")
    entered_password = input("Please enter your password: ")
    return entered_password

def dump_messages():
    global list_of_messages
    while len(list_of_messages) > 0:
        message = list_of_messages.pop(0)
        if(message['class']=='group invite' or message['class']=='group update'):
            groupname = message["group name"]
            ks_response = group_keys_update(message)
            if(ks_response["command"] == "PUBKEY"):
                to_user_pubkey = crypto.str_to_key(ks_response["pubkey"])
                crypto.export_key(to_user_pubkey, f"mykeys/{username}_{groupname}_pub_key.pem")
                if(groupname in prev_users):
                    prev_users.remove(groupname)
                prev_users.append(groupname)
                print_message(message)
            else:
                log("Keyserver returned an error")
                print("[ERROR] Key server returned an error!")
        else:
            print_message(message)

def authenticate_password(password):
    # server_connection.send(to_send({"command": "password authenticate", "password": password}))
    # print(f"SENT to {server_connection.getpeername()}")
    server_connection.send(to_send({"command": "password authenticate lvl1", "username": username}))
    log(f"first level authentication password sent")
    response = from_recv(server_connection.recv(4096))
    assert response["command"] == "password authenticate lvl2"
    # fp(response["aes_key"])
    log(f"aes key received in response: {response['aes_key']}")
    aes_key = decryptData(response["aes_key"], username, True)
    aes_iv = decryptData(response["aes_iv"], username, True)
    log("[DEBUG] RECEIVED aes_key & aes_iv")
    server_connection.send(to_send({"command": "password authenticate lvl3", "username": username, "encrypted password": b64encode(crypto.encryptAES(aes_key, aes_iv, password.encode())).decode()}))
    log("password sent for final authentication")

def gen_and_send_key():
    log("[DEBUG] Registering to KeyServer")
    ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ks.connect(('localhost', KEYSERVER_PORT))
    pub_key, priv_key = crypto.gen_RSA_keys()
    crypto.export_key(pub_key, f"mykeys/{username}_pub_key.pem")
    crypto.export_key(priv_key, f"mykeys/{username}_priv_key.pem")
    ks.send(to_send({"command": "STORE", "username": username, "key": crypto.key_to_str(pub_key), 'type':'fastchatter'}))
    log(f"SENT to KEYSERVER")
    response = from_recv(ks.recv(4096))
    log(f"{response['command']}, {response['msg']}")

def group_keys_update(message):
    log(f"group invite/update found! Group: {message['group name']}")
    grp_priv_key = crypto.str_to_key(decryptData(message["encrypted message"], username))
    groupname = message["group name"]
    crypto.export_key(grp_priv_key, f"mykeys/{username}_{groupname}_priv_key.pem")

    log('storing/updating public key in local storage, contacting keyserver')
    ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ks.connect(('localhost', KEYSERVER_PORT))
    ks.send(to_send({"command": "RETRIEVE", "username": groupname, 'type':'group'}))
    ks_response = from_recv(ks.recv(4096))
    return ks_response

def download_image(image):
    if(image['class']=='group message'):
        log(f"this is a group image from {image['group name']}")
        groupname = image["group name"]
        filename = decryptData(image["filename"], username+"_"+groupname)
        file = open("images/"+filename, 'wb')
        file.write(decryptData(image["encrypted message"], username+"_"+groupname, True))
        file.close()
        print(f'{image["group name"]}:{image["sender username"]}: Downloaded {filename}')

    elif(image['class']=='user message'):
        log(f"this is an individual image from {image['receiver username']}")
        filename = decryptData(image["filename"], username)
        file = open("images/"+filename, 'wb')
        file.write(decryptData(image["encrypted message"], username, True))
        file.close()
    # b64_to_img(image["encrypted message"], "images/"+image["filename"])
        print(f'{image["sender username"]}: Downloaded {filename}')

def prompt_group_gen():
    groupname = input("Enter groupname: ")
    log(f"user wishes to create group with name: {groupname}")
    members = take_user_list()
    log(f"[DEBUG] members to be added: {members}")
    return groupname, members

def send_group_key(username, groupname):
    ks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ks.connect(('localhost', KEYSERVER_PORT))
    pub_key, priv_key = crypto.gen_RSA_keys()
    crypto.export_key(pub_key, f"mykeys/{username}_{groupname}_pub_key.pem")
    crypto.export_key(priv_key, f"mykeys/{username}_{groupname}_priv_key.pem")
    ks.send(to_send({"command": "STORE", "username": groupname, "key": crypto.key_to_str(pub_key), 'type':'group'}))
    return priv_key

def send_group_message(to_groupname, message):
    encrypted_message = encryptData(message, to_groupname, type="group")
    log("message encrypted")
    server_connection.send(to_send({"command": "user-user message","type": "message", "encrypted message": encrypted_message, "receiver username": '', "sender username": username, "class":"group message", "group name": to_groupname, "time_sent" : str(time.ctime())}))
    response = from_recv(server_connection.recv(4096))
    if(response["command"]) == "error, bad member":
        print("You are not a member of this group")
        log(f"user was not member of group {to_groupname}")
    else:
        log("Group message sent!")

def add_members():
    global server_connection
    members = take_user_list()
    log(f"user attempting to add members: {members} to group: {groupname}")
    server_connection.send(to_send({"command":"add to group", "group name":groupname, "member list":members}))
    response = from_recv(server_connection.recv(4096))
    if(response["command"]=="error, bad admin"):
        print("You are not admin for this group!")
        log("user was not group admin")
        return False, []
    log(f"sent add member request to server")
    return True, members

def take_user_list():
    input_list = input("Enter comma separated list of members: ")
    arr = input_list.split(",")
    members = []
    for i in arr:
        members.append(i.strip())
    return members

def send_priv_key_updation_of_members(members, group_invite_or_update):
    priv_key = crypto.import_key(f"mykeys/{username}_{groupname}_priv_key.pem")
    for member in members:
        encrypted_key = encryptData(crypto.key_to_str(priv_key), member)
        server_connection.send(to_send({'command':'user-user message', 'encrypted message':encrypted_key, 'receiver username':member, 'sender username':username, 'type':'message', 'class':group_invite_or_update, 'group name':groupname, "time_sent" : str(time.ctime())}))                
        log(f'[DEBUG] sent private key for group to member: {member}')

def remove_members():
    global server_connection
    members = take_user_list() #will ignore any members entered but not in group
    log(f"user attempting to remove members: {members} to group: {groupname}")
    server_connection.send(to_send({"command":"remove from group", "group name":groupname, "member list":members}))
    response = from_recv(server_connection.recv(4096))
    if(response["command"]=="error, bad admin"):
        print("You are not admin for this group!")
        log("user was not group admin")
        return False, []
    log("sent member remove command to server")
    members = response["members"]
    log(f"received list of remaining members in group: {members}")
    return True, members

username = input("Enter a username: ")
logfd = open(f"logs/clients_logs/client{username}__{int(time.time())}.log", 'w')

initial = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
initial.connect(('localhost', LOAD_BALANCER_PORT))
lb_response = from_recv(initial.recv(1024))
token = lb_response["token"]
server_port = lb_response["server port"]
log(f"load balancer has returned token:{token} and server port to connect to:{server_port}")
#fp(token)
#fp(server_port)
server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_connection.connect(('localhost', server_port))
# print(username)
server_connection.send(to_send({"command": "first connection", "authentication token": token, "username": username}))
log(f"Sent first connection to server with username: {username} and token: {token}")
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
            data = s.recv(4096)
            log(f"incoming data from server! {data.decode()}")
            if not data:
                print('Server Disconnected!')
                sys.exit()
            response = from_recv(data)
            command = response["command"]

            if command == "new user":
                handle_new_user(server_sock = server_connection)

            elif command == "existing user" or command == "re-enter":
                entered_password = prompt_for_password(command)
                authenticate_password(entered_password)

            elif command == "register for keyServer":
                gen_and_send_key()
                print_menu()

            elif command == "pending messages":
                print("Password Authenticated!")
                log("Password authentication complete, pending messages incoming!")
                messages = response["messages"]
                display_pending_messages(messages)
                print_menu()

            elif command == "user-user message":
                if response["type"] == "message":
                    list_of_messages.append(response)
                    log(f"received message from {response['receiver username']}. Stored ")
                elif response["type"] == "image":
                    list_of_images.append(response)
                    log(f"received image from {response['receiver username']}. Stored ")

        else:
            command  = sys.stdin.readline().strip()
            log(f"User has made an input! It is {command}")

            if command == '1':
                # from_user = input("Enter username whose messages you want to read: ")
                print(f"You have {len(list_of_messages)} unread messages!")
                log("user is reading unread messages!")
                dump_messages()
                    
            elif command == '2':
                print(f"Downloading {len(list_of_images)} images!")
                log("user is downloading images")
                while len(list_of_images) > 0:
                    image = list_of_images.pop(0)
                    download_image(image)

            elif command == '3':
                to_username = input("Enter to username: ")
                log(f"user sending message to user {to_username}")
                message = input("Enter message: ")
                try:
                    encrypted_message = encryptData(message, to_username)
                    log("encrypted message")
                    server_connection.send(to_send({"command": "user-user message","type": "message", "encrypted message": encrypted_message, "receiver username": to_username, "sender username": username, "class":"user message", "time_sent" : str(time.ctime())}))
                    log("sent message to server")
                except Exception as e:
                    log(e)
                    log("[WARNING] Connection to keyserver compromised! Not sending!")
                    print("[WARNING] Connection to keyserver compromised! Not sending!")

            elif command == '4':
                to_username = input("Enter to username: ")
                log(f"user sending image to user {to_username}")
                filename = input("Enter filename: ")
                try:
                    file = open(filename, 'rb')
                    image = file.read()
                    file.close()
                    log("file provided by user read!")
                    try:
                        server_connection.send(to_send({"command": "user-user message", "type": "image", "filename": encryptData(os.path.basename(filename), to_username), "encrypted message": encryptData(image, to_username, True), "class" : "user message", "receiver username": to_username, "sender username": username, "time_sent" : str(time.ctime())}))
                        log("image sent to server")
                    except Exception as e:
                        log(e)
                        log("[WARNING] Connection to keyserver compromised! Not sending!")
                        print("[WARNING] Connection to keyserver compromised! Not sending!")
                except:
                    log(f"[ERROR] {filename} does not exist!")
                    print(f"[ERROR] {filename} does not exist!")

            elif command == '5':
                to_groupname = input("Enter to groupname: ")
                log(f"user sending message to group {to_groupname}")
                message = input("Enter message: ")
                try:
                    send_group_message(to_groupname, message)
                except Exception as e:
                    log(e)
                    log("[WARNING] Connection to keyserver compromised! Not sending!")
                    print("[WARNING] Connection to keyserver compromised! Not sending!")

            elif command == '6':
                to_groupname = input("Enter to groupname: ")
                log(f"user sending image to group {to_groupname}")
                filename = input("Enter filename: ")
                try:
                    file = open(filename, 'rb')
                    image = file.read()
                    file.close()
                    try:
                        server_connection.send(to_send({"command": "user-user message", "type": "image", "filename": encryptData(os.path.basename(filename), to_groupname, type='group'), "encrypted message": encryptData(image, to_groupname, True, type='group'), "receiver username": "", "sender username": username, "class":"group message" ,"group name":to_groupname, "time_sent" : str(time.ctime())}))
                        response = from_recv(server_connection.recv(4096))
                        if(response["command"]) == "error, bad member":
                            print("You are not a member of this group")
                            log(f"user was not member of group {to_groupname}")
                        else:
                            log("Group image sent!")
                    except Exception as e:
                        log(e)
                        log("[WARNING] Connection to keyserver compromised! Not sending!")
                        print("[WARNING] Connection to keyserver compromised! Not sending!")
                except:
                    log(f"[ERROR] {filename} does not exist!")
                    print(f"[ERROR] {filename} does not exist!")

            elif command == '7':
                #wish to create group
                name, members = prompt_group_gen()
                group_priv_key = send_group_key(username = username, groupname = name)
                log(f"Created group public key and sent to KEYSERVER")
                server_connection.send(to_send({"command":"create group", "group name":name, "admin":username, "member list":members+[username]}))
                log("[DEBUG] sent group creation request to servers")

                for member in members:
                    encrypted_key = encryptData(crypto.key_to_str(group_priv_key), member)
                    server_connection.send(to_send({'command':'user-user message', 'encrypted message':encrypted_key, 'receiver username':member, 'sender username':username, 'type':'message', 'class':'group invite', 'group name':name, 'time_sent' : str(time.ctime())}))
                    log(f'[DEBUG] sent private key for group to member: {member}')
                
            elif command == '8':
                groupname = input("Enter groupname: ")
                log("user attempting to update group details!")
                add_choice = input("Would you like to add or remove members? (enter 1 for add and 2 for remove): ")
                if(add_choice=='1'):
                    flag, members = add_members()
                    if flag:
                        send_priv_key_updation_of_members(members, 'group invite')
                
                elif(add_choice=='2'):
                    flag, members = remove_members()
                    if flag:
                        send_group_key(username = username, groupname = groupname)
                        log(f"Created new public key for group and sent to KEYSERVER")
                        send_priv_key_updation_of_members(members, 'group update')
                    
                else:
                    print('invalid choice')
                    log("user entered invalid choice")
                    continue

            elif command == '9':
                log("closing connection")
                # server_connection.close()
                sys.exit()

            else:
                log("user entered invalid choice")
                print("Invalid command!")
            print_menu()