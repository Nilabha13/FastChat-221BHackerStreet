import json
import datetime
import os
from struct import pack, unpack

def to_send(dict):
	"""Converts the supplied dictionary into appropriate JSON format

	:param dict: The dictionary to be converted
	:type dict: dict
	:return: The dictionary in JSON format
	:rtype: bytes
	"""
	return json.dumps(dict).encode()

def from_recv(data):
	"""Converts the supplied JSON data to a dictionary

	:param data: The data in JSON format
	:type data: bytes
	:return: The data in a dictionary
	:rtype: dict
	"""
	return json.loads(data.decode())

def fp(data): # Fake function
    print(f"[DEBUG] {data} TYPE:{type(data)}")

def log_to_file(msg, fd):
	"""Logs the supplied message to the file specified

	:param msg: The message to be logged
	:type msg: str
	:param fd: The file to log to
	:type fd: _io.TextIOWrapper
	"""
	fd.write(f"[{str(datetime.datetime.now())}] {msg}\n")
	fd.flush()

def create_dir_if_not_exists(dir):
	"""Checks if the supplied directory already exists; creates the directory if it doesn't exist.

	:param dir: The directory
	:type dir: str
	"""
	if not os.path.isdir(dir):
		os.makedirs(dir)

def create_dirs_if_not_exist_recursive(dir_seq):

	dir_so_far = ''
	for dir in dir_seq:
		dir_so_far = os.path.join(dir_so_far, dir)
		create_dir_if_not_exists(dir_so_far)

def my_send(sock, to_send):
	length = pack('>Q', len(to_send))
	print(f"Sending {len(to_send)} bytes")
	sock.sendall(length)
	sock.sendall(to_send)

def my_recv(sock, buff_size):
	byte_size = sock.recv(8)
	(length,) = unpack('>Q', byte_size)
	data = b''
	while len(data) < length:
		to_read = length - len(data)
		data += sock.recv(buff_size if to_read > buff_size else to_read)
	return data
