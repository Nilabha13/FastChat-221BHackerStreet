import json
from base64 import b64encode, b64decode

def to_send(dict):
	return json.dumps(dict).encode()

def from_recv(data):
	return json.loads(data.decode())

def img_to_b64(filename):
	file = open(filename, 'rb')
	img = file.read()
	file.close()
	return b64encode(img).decode()

def b64_to_img(data, filename):
	img = b64decode(data.encode())
	file = open(filename, 'wb')
	file.write(img)
	file.close()