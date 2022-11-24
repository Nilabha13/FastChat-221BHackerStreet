from pwn import *

for i in range(10):
    target = process(["python3", "fake_client.py"])
    target.recv(4096)
    target.sendline(f"a{i}".encode())
    target.recv(4096)
    target.sendline(f"r{i}".encode())
    target.recv(4096)
    target.close()