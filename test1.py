from pwn import *
from message_patterns import *

def pwnsend(msg, target):
    print(msg)
    target.sendline(msg.encode())

def pwnrecv(text, target):
    msg = target.recv(4096).decode()
    # print(msg)
    return(msg)

def pwnrecv2(text, target):
    msg = target.recv(4096).decode()
    # print(msg)
    return(msg)

def pwnrecv3(text, target):
    msg = target.recvuntil(text.encode()).decode()
    print(msg)
    return(msg)


def send_message_across_clients(sender_num, receiver_num, text):
    sender = list_of_processes[sender_num]
    pwnsend("3", sender)
    pwnrecv("", sender)
    pwnsend(list_of_ids[receiver_num], sender)
    pwnrecv("", sender)
    pwnsend(text, sender)
    pwnrecv("", sender)

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
        pwnrecv("QUIT", target)
        list_of_ids.append(f"a{i}")
        list_of_processes.append(target)

    message_queue = exponential_time_delay(10,5,10)
    for message_data in message_queue:
        time.sleep(message_data[2])
        send_message_across_clients(message_data[0], message_data[1], "speedtest!")
        # time.sleep(message_data[2])
    time.sleep(message_data[2])

    for i in range(n):
        list_of_processes[i].close()
        print(f"process {i} closed")

def create_groups():
    pass

def login_simultaneous_users_and_grp_message():
    pass


# create_simultaneous_users_and_close(10)
login_simultaneous_users_and_individual_message(10)

