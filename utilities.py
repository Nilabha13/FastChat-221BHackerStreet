import json
import datetime
import os
from struct import pack, unpack
from matplotlib import pyplot as plt


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
	"""Checks if supplied nested directories already exists; creates the directories which do not exist.

	:param dir_seq: The sequence of nested directories in the path
	:type dir_seq: list
	"""
	dir_so_far = ''
	for dir in dir_seq:
		dir_so_far = os.path.join(dir_so_far, dir)
		create_dir_if_not_exists(dir_so_far)


def my_send(sock, to_send):
	"""A send function with the capabilities of sending large data.

	:param sock: The socket through which the data would be sent
	:type sock: socket.socket
	:param to_send: The data to be sent
	:type to_send: bytes
	"""
	length = pack('>Q', len(to_send))
	sock.sendall(length)
	sock.sendall(to_send)


def my_recv(sock, buff_size):
	"""A receive function with the capabilities of receiving large data.

	:param sock: The socket through which the data is received
	:type sock: socket.socket
	:param buff_size: The chunk size of the buffer
	:type buff_size: int
	:return: The complete data received from the socket
	:rtype: bytes
	"""
	byte_size = sock.recv(8)
	(length,) = unpack('>Q', byte_size)
	data = b''
	while len(data) < length:
		to_read = length - len(data)
		data += sock.recv(buff_size if to_read > buff_size else to_read)
	return data


def plot_histogram(data, lower, upper, bin_width):
	"""A function to plot histograms.

	:param data: The data on whcich the histogram is plotted
	:type data: list
	:param lower: The lower limit of the histogram
	:type lower: int / float
	:param upper: The upper limit of the histogram
	:type upper: int / float
	:param bin_width: The bin-width of the histogram
	:type bin_width: int / floar
	"""
	plt.hist(data, bins=range(lower, upper, bin_width), color='green')
	plt.show()

def plot_time_variation(data):
	"""A function to plot time variation of data

	:param data: The data on whcich the variation is plotted
	:type data: list
	"""
	plt.plot(data)
	plt.plot(data)
	plt.show()