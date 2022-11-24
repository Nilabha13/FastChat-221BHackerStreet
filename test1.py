from pwn import *
from message_patterns import *
import os
import datetime


def pwnsend(msg, target):
    print(msg)
    target.sendline(msg.encode())

def pwnrecv(text, target):
    msg = target.recv(4096).decode()
    # print(msg)
    return(msg)

# def pwnrecv2(text, target):
#     msg = target.recv(4096).decode()
#     # print(msg)
#     return(msg)

# def pwnrecv3(text, target):
#     msg = target.recvuntil(text.encode()).decode()
#     print(msg)
#     return(msg)


def send_message_across_clients(sender_num, receiver_num, text, is_image):
    sender = list_of_processes[sender_num]
    receiver = list_of_processes[receiver_num]
    sender_name = list_of_ids[sender_num]
    receiver_name = list_of_ids[receiver_num]

    if(not is_image):
        pwnsend("3", sender)
        pwnrecv("", sender)
        pwnsend(receiver_name, sender)
        pwnrecv("", sender)
        pwnsend(text, sender)
        pwnrecv("", sender)
    else:
        pwnsend("4", sender)
        pwnrecv("", sender)
        pwnsend(receiver_name, sender)
        pwnrecv("", sender)
        pwnsend("icon.png", sender)
        pwnrecv("", sender)
    
    return (sender_name,receiver_name, is_image)


def measure_times(username_message_queue):
    list_of_client_logs = {} #dictionary mapping username to filename
    all_client_logs = os.listdir("logs/clients_logs")
    all_client_logs.sort()
    for client_log in all_client_logs:
        client_log2 = client_log[6:]
        data = client_log2.split("__")
        data2 = '__'.join(data[:-1])
        list_of_client_logs[data2]=client_log
    # print(list_of_client_logs)
    print(username_message_queue)

    sent_log_statements={}
    received_log_statements={}

    for client in list_of_client_logs:
        with open("logs/clients_logs/"+list_of_client_logs[client], 'r') as sender_log_file:
            for line in sender_log_file:
                if("user sending message to user" in line or "user sending image to user" in line):
                    if(client in sent_log_statements):
                        sent_log_statements[client].append(line)
                    else:
                        sent_log_statements[client] = [line]


        with open("logs/clients_logs/"+list_of_client_logs[client], 'r') as receiver_log_file:
            for line in receiver_log_file:
                if("received message from" in line or "received image from" in line):
                    if(client in received_log_statements):
                        received_log_statements[client].append(line)
                    else:
                        received_log_statements[client] = [line]
    

    sum = 0
    for message_element in username_message_queue:
        print()
        sent_statement = sent_log_statements[message_element[0]][0].split(']')[0].strip('[')
        received_statement = received_log_statements[message_element[1]][0].split(']')[0].strip('[')
        # print(sent_statement)
        # print(received_statement)
        t1 = datetime.datetime.strptime(sent_statement, "%Y-%m-%d %H:%M:%S.%f")
        t2 = datetime.datetime.strptime(received_statement, "%Y-%m-%d %H:%M:%S.%f")
        dt = (t2-t1).microseconds /1000
        print("time:", dt, 'ms')
        sum += dt
        print()

        sent_log_statements[message_element[0]] = sent_log_statements[message_element[0]][1:]

        received_log_statements[message_element[1]] = received_log_statements[message_element[1]][1:]
    
    print("avg time: ", sum/len(username_message_queue), "ms")



# lets create such groups: g1 has members 0:n-1, g2 has members m:m+n-1 and so on untill k groups.

def create_group(admin_num, group_name, members_list):
    input_string = ""
    for i in members_list:
        input_string = input_string+list_of_ids[i]+','
    input_string= input_string.rstrip(',')
    # print(input_string)

    admin = list_of_processes[admin_num]
    pwnsend("7",admin)
    pwnrecv("", admin)
    pwnsend(group_name, admin)
    pwnrecv("", admin)
    pwnsend(input_string, admin)
    pwnrecv("", admin)

    for i in members_list:
        pwnsend("1", list_of_processes[i])
        pwnrecv("", list_of_processes[i])




def create_consecutive_users_and_close(n):
    for i in range(n):
        target = process(["python3", "fake_client.py"])
        pwnrecv("username:", target)
        # time.sleep(1)
        pwnsend(f"a{i}", target)
        pwnrecv("password:", target)
        pwnsend(f"r{i}", target)
        pwnrecv(")", target)
        # time.sleep(1)
        pwnrecv("QUIT", target)
        target.close()
        print("closed this process")

def create_simultaneous_users_and_close(n):
    list_of_processes = []
    for i in range(n):
        target = process(["python3", "fake_client.py"])
        pwnrecv("username:", target)
        # time.sleep(1)
        pwnsend(f"a{i}", target)
        pwnrecv("password:", target)
        pwnsend(f"r{i}", target)
        # pwnrecv(")", target)
        # time.sleep(1)
        pwnrecv("QUIT", target)
        list_of_processes.append(target)

    for i in range(n):
        list_of_processes[i].close()
        print(f"process {i} closed")

def login_simultaneous_users_and_individual_message(n):
    global list_of_ids
    global list_of_processes
    global message_queue
    global username_message_queue
    list_of_processes = []
    list_of_ids = []
    for i in range(n):
        target = process(["python3", "fake_client.py"])
        pwnrecv("username:", target)
        # time.sleep(1)
        pwnsend(f"a{i}", target)
        pwnrecv("password:", target)
        pwnsend(f"r{i}", target)
        # pwnrecv(")", target)
        # time.sleep(1)
        time.sleep(0.05)
        pwnrecv("QUIT", target)
        list_of_ids.append(f"a{i}")
        list_of_processes.append(target)

    message_queue = exponential_time_delay(200,200,1000)
    username_message_queue = []
    for message_data in message_queue:
        time.sleep(message_data[2])
        message_tracking_object = send_message_across_clients(message_data[0], message_data[1], "speedtest!", message_data[3])
        username_message_queue.append(message_tracking_object)
        
        # time.sleep(message_data[2])
    time.sleep(message_data[2])

    for i in range(n):
        list_of_processes[i].close()
        print(f"process {i} closed")



def login_simultaneous_users_and_individual_message_not_well_behaved(n, message_gap):
    global list_of_ids
    global list_of_processes
    global message_queue
    global username_message_queue
    list_of_processes = []
    list_of_ids = []
    for i in range(n):
        target = process(["python3", "fake_client.py"])
        pwnrecv("username:", target)
        # time.sleep(1)
        pwnsend(f"a{i}", target)
        pwnrecv("password:", target)
        pwnsend(f"r{i}", target)
        # pwnrecv(")", target)
        # time.sleep(1)
        time.sleep(0.2)
        pwnrecv("QUIT", target)
        list_of_ids.append(f"a{i}")
        list_of_processes.append(target)

    message_queue = exponential_time_delay(60,20,180)
    username_message_queue = []
    counter = 0
    user_to_kill = 0
    users_killed = []
    for message_data in message_queue:
        if(counter>message_gap):
            counter = 0
            list_of_processes[user_to_kill].close()
            users_killed.append(user_to_kill)
            user_to_kill+=1
        if(message_data[0] not in users_killed and message_data[1] not in users_killed):
            time.sleep(message_data[2])
            message_tracking_object = send_message_across_clients(message_data[0], message_data[1], "speedtest!", message_data[3])
            time.sleep(message_data[2])
            username_message_queue.append(message_tracking_object)
            counter+=1

        # time.sleep(message_data[2])
    time.sleep(message_data[2])

    for i in range(n):
        if(i not in users_killed):
            list_of_processes[i].close()
            print(f"process {i} closed")



def login_simultaneous_users_and_individual_message_image(n):
    global list_of_ids
    global list_of_processes
    global message_queue
    global username_message_queue
    list_of_processes = []
    list_of_ids = []
    for i in range(n):
        target = process(["python3", "fake_client.py"])
        pwnrecv("username:", target)
        # time.sleep(1)
        pwnsend(f"a{i}", target)
        pwnrecv("password:", target)
        pwnsend(f"r{i}", target)
        # pwnrecv(")", target)
        # time.sleep(1)
        time.sleep(0.2)
        pwnrecv("QUIT", target)
        list_of_ids.append(f"a{i}")
        list_of_processes.append(target)

    message_queue = exponential_time_delay(100,40,200, True, 1)
    username_message_queue = []
    for message_data in message_queue:
        time.sleep(message_data[2])
            
        message_tracking_object = send_message_across_clients(message_data[0], message_data[1], "speedtest!", message_data[3])
        username_message_queue.append(message_tracking_object)
        
        # time.sleep(message_data[2])
    time.sleep(message_data[2])

    for i in range(n):
        list_of_processes[i].close()
        print(f"process {i} closed")


def login_and_create_groups(n):
    global list_of_ids
    global list_of_processes
    global message_queue
    global username_message_queue
    list_of_processes = []
    list_of_ids = []
    for i in range(n):
        target = process(["python3", "fake_client.py"])
        pwnrecv("username:", target)
        # time.sleep(1)
        pwnsend(f"a{i}", target)
        pwnrecv("password:", target)
        pwnsend(f"r{i}", target)
        # pwnrecv(")", target)
        # time.sleep(1)
        time.sleep(0.2)
        pwnrecv("QUIT", target)
        list_of_ids.append(f"a{i}")
        list_of_processes.append(target)
    
    create_groups()


def create_groups():
    group_list = group_creation_sample(5,2,5) ## can see what these are in message_patterns.py
    for group in group_list:
        create_group(group[0], group[2], group[1])








def login_simultaneous_users_and_grp_message():
    pass





# create_simultaneous_users_and_close(100)
# login_simultaneous_users_and_individual_message(10)

# login_simultaneous_users_and_individual_message_not_well_behaved(60, 6)

# login_simultaneous_users_and_individual_message_image(100)
login_and_create_groups(30)


# measure_times(username_message_queue)






















