from pwn import *

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

create_consecutive_users_and_close(10)

