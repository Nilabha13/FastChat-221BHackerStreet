from pwn import *
from message_patterns import *
import os
import datetime
import statistics
from utilities import *


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


def send_grp_message(grp_id, member_id, text):
    group_name = group_list[grp_id]
    sender = list_of_processes[group_members[group_name][member_id]]
    sender_name = list_of_ids[group_members[group_name][member_id]]

    pwnsend("5", sender)
    pwnrecv("", sender)
    pwnsend(group_name, sender)
    pwnrecv("", sender)
    pwnsend(text, sender)
    pwnrecv("", sender)

    return group_name, sender_name



def measure_times_individual(username_message_queue):
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
    print(group_members)

    sent_log_statements={}
    received_log_statements={}

    for client in list_of_client_logs:
        with open("logs/clients_logs/"+list_of_client_logs[client], 'r') as sender_log_file:
            for line in sender_log_file:
                if("user sending message to user" in line or "user sending image to user" in line):
                    print(line)
                    if(client in sent_log_statements):
                        sent_log_statements[client].append(line)
                    else:
                        sent_log_statements[client] = [line]


        with open("logs/clients_logs/"+list_of_client_logs[client], 'r') as receiver_log_file:
            for line in receiver_log_file:
                if("received message from" in line or "received image from" in line):
                    print(line)
                    if(client in received_log_statements):
                        received_log_statements[client].append(line)
                    else:
                        received_log_statements[client] = [line]
    

    count=0
    lost_count=0
    t_list = []
    for message_element in username_message_queue:
        try:
            print()
            for i in sent_log_statements[message_element[0]]:
                if(message_element[1] in i):
                    sent_statement_og = i
                    sent_statement = i.split(']')[0].strip('[')
                    break
            # sent_statement = sent_log_statements[message_element[0]][0].split(']')[0].strip('[')
            for i in received_log_statements[message_element[1]]:
                if(message_element[0] in i):
                    received_statement_og = i
                    received_statement = i.split(']')[0].strip('[')

                    break
            # print(sent_statement)
            # print(received_statement)
            t1 = datetime.datetime.strptime(sent_statement, "%Y-%m-%d %H:%M:%S.%f")
            t2 = datetime.datetime.strptime(received_statement, "%Y-%m-%d %H:%M:%S.%f")
            dt = (t2-t1).microseconds /1000
            print("time:", dt, 'ms')
            # sum += dt
            print()

            sent_log_statements[message_element[0]].remove(sent_statement_og)

            received_log_statements[message_element[1]].remove(received_statement_og)
            t_list.append(dt)
            count+=1
        except Exception as e:
            print(message_element)
            print(e)
            lost_count+=1
    
    print("messages sent through: ", count)
    print("avg time: ", statistics.mean(t_list), "ms")
    print("median time: ", statistics.median(t_list), "ms")
    print("stdev time: ", statistics.stdev(t_list), "ms")
    print("messages lost: ", lost_count)
    plot_histogram(t_list,0,100, 5)


def measure_times_group(grp_user_message_queue):
    list_of_client_logs = {} #dictionary mapping username to filename
    all_client_logs = os.listdir("logs/clients_logs")
    all_client_logs.sort()
    for client_log in all_client_logs:
        client_log2 = client_log[6:]
        data = client_log2.split("__")
        data2 = '__'.join(data[:-1])
        list_of_client_logs[data2]=client_log
    # print(list_of_client_logs)
    # print(list_of_client_logs)
    print(grp_user_message_queue)

    sent_log_statements={}
    received_log_statements={}

    for client in list_of_client_logs:
        with open("logs/clients_logs/"+list_of_client_logs[client], 'r') as sender_log_file:
            for line in sender_log_file:
                if("user sending message to group" in line or "user sending image to group" in line):
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
        
    t_list = []
    count = 0
    lost_count = 0
    for message in grp_user_message_queue:
        t = False
        try:
            grp_name = message[0]
            sender = message[1]
            receiver_list = group_members[grp_name]
            
            for statement in sent_log_statements[sender]:
                if(grp_name) in statement:
                    sent_statement_og = statement
                    sent_time = statement.split(']')[0].strip('[')
                    break
            sent_log_statements[sender].remove(sent_statement_og)
            t = True

            t1 = datetime.datetime.strptime(sent_time, "%Y-%m-%d %H:%M:%S.%f")

            for receiver_num in receiver_list:
                if not (list_of_ids[receiver_num] == sender):
                    receiver_name = list_of_ids[receiver_num]
                    for statement in received_log_statements[receiver_name]:
                        if(grp_name in statement and sender in statement):
                            received_statement_og = statement
                            received_time = statement.split(']')[0].strip('[')
                            break
                    received_log_statements[receiver_name].remove(received_statement_og)
                    t2 = datetime.datetime.strptime(received_time, "%Y-%m-%d %H:%M:%S.%f")
                    dt = (t2-t1).microseconds/1000
                    count+=1
                    t_list.append(dt)
        except Exception as e:
            if(not t):
                print("removing: ", sent_statement_og, "from", sent_log_statements[sender])
            else:
                print("removing: ", received_statement_og, "from", received_log_statements[receiver_name])
                print(receiver_name)
            print(message)
            print(e)
            lost_count+=1
            
    
    print("messages sent through: ", count)
    print("avg time: ", statistics.mean(t_list), "ms")
    print("median time: ", statistics.median(t_list), "ms")
    print("stdev time: ", statistics.stdev(t_list), "ms")
    print("messages lost: ", lost_count)
    plot_histogram(t_list,0,100, 5)


        




group_list = []
group_members = {}


# lets create such groups: g1 has members 0:n-1, g2 has members m:m+n-1 and so on untill k groups.

def create_group(admin_num, group_name, members_list):
    global group_list
    global group_members
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
    group_list.append(group_name)
    time.sleep(0.1)

    member_num_list = []

    for i in members_list:
        time.sleep(0.1)
        pwnsend("1", list_of_processes[i])
        time.sleep(0.1)
        pwnrecv("", list_of_processes[i])
        member_num_list.append(i)
        time.sleep(0.1)

    group_members[group_name] = member_num_list



def fake_create_group(admin_num, group_name, members_list):
    global group_list
    global group_members
    input_string = ""
    for i in members_list:
        input_string = input_string+list_of_ids[i]+','
    input_string= input_string.rstrip(',')
    # print(input_string)

    # admin = list_of_processes[admin_num]
    # pwnsend("7",admin)
    # pwnrecv("", admin)
    # pwnsend(group_name, admin)
    # pwnrecv("", admin)
    # pwnsend(input_string, admin)
    # pwnrecv("", admin)
    group_list.append(group_name)

    member_num_list = []

    for i in members_list:
        # pwnsend("1", list_of_processes[i])
        # pwnrecv("", list_of_processes[i])
        member_num_list.append(i)
    group_members[group_name] = member_num_list











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

    message_queue = fake_exponential_time_delay(20,70,250, 1/150)
    # message_queue = i_only_talk_to_bestie(30,10,3,20,0.005)
    username_message_queue = []
    for message_data in message_queue:
        time.sleep(message_data[2])
        print(message_data)
        message_tracking_object = send_message_across_clients(message_data[0], message_data[1], "speedtest!", message_data[3])
        username_message_queue.append(message_tracking_object)
        
        # time.sleep(message_data[2])
    time.sleep(1)

    for i in range(n):
        list_of_processes[i].close()
        print(f"process {i} closed")
        time.sleep(0.05)



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

    message_queue = heavyweight_users(100,1/200)
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
    global grp_user_message_queue
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
    
    num_groups = 5
    num_members = 6
    overlap = 3
    create_groups(num_groups, num_members, overlap)

    # grp_message_list = fake_exponential_time_delay_groups(num_groups, num_members, 3, 5, 1/20)

    # grp_user_message_queue = []

    # for group_message in grp_message_list:

    #     grp_name, user_name = send_grp_message(group_message[0], group_message[1], "group speedtest!")
    #     grp_user_message_queue.append((grp_name, user_name))
    
    # "user sending message to group <groupname>"
    # "received message from <username> on <groupname>"

    time.sleep(1)

    for i in range(n):
        list_of_processes[i].close()
        print(f"process {i} closed")
        time.sleep(0.05)




def create_groups(num_groups, num_members, overlap):
    group_list = group_creation_sample(num_members,overlap,num_groups) ## can see what these are in message_patterns.py
    for group in group_list:
        create_group(group[0], group[2], group[1])

def fake_create_groups(num_groups, num_members, overlap):
    group_list = group_creation_sample(num_members,overlap,num_groups) ## can see what these are in message_patterns.py
    for group in group_list:
        fake_create_group(group[0], group[2], group[1])



def login_and_grp_messages(n):
    global list_of_ids
    global list_of_processes
    global message_queue
    global username_message_queue
    global grp_user_message_queue
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
    
    num_groups = 5
    num_members = 6
    overlap = 3
    fake_create_groups(num_groups, num_members, overlap)

    grp_message_list = fake_exponential_time_delay_groups(num_groups, num_members, 20, 500, 1/80)
    grp_message_list = groups_transversal(num_groups, num_members, 100 ,1/40)

    grp_user_message_queue = []

    for group_message in grp_message_list:

        grp_name, user_name = send_grp_message(group_message[0], group_message[1], "group speedtest!")
        grp_user_message_queue.append((grp_name, user_name))
    
    # "user sending message to group <groupname>"
    # "received message from <username> on <groupname>"

    time.sleep(1)

    for i in range(n):
        list_of_processes[i].close()
        print(f"process {i} closed")
        time.sleep(0.05)





# create_simultaneous_users_and_close(100)
# login_simultaneous_users_and_individual_message(20)

# login_simultaneous_users_and_individual_message_not_well_behaved(60, 6)

login_simultaneous_users_and_individual_message_image(100)
# login_and_create_groups(30)
# login_and_grp_messages(30)
# print(group_members)



measure_times_individual(username_message_queue)
# measure_times_group(grp_user_message_queue=grp_user_message_queue)






















