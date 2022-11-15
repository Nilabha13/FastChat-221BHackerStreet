import json

def to_send(dict):
	return json.dumps(dict).encode()

def from_recv(data):
	return json.loads(data.decode())