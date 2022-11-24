import json
import datetime

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