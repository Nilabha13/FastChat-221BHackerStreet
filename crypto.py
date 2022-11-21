import bcrypt
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from hashlib import sha256


# RSA Key Handling

def gen_RSA_keys():
    keys = RSA.generate(2048)
    return keys.public_key(), keys

def export_key(key, filename):
    keyfile = open(filename, 'wb')
    keyfile.write(key.export_key('PEM'))
    keyfile.close()

def import_key(filename):
    keyfile = open(filename, 'r')
    key = RSA.import_key(keyfile.read())
    keyfile.close()
    return key

def key_to_str(key):
    return key.export_key('PEM').decode()

def str_to_key(data):
    return RSA.import_key(data.encode())


# AES Key Handling

def gen_AES_key_iv():
	key = get_random_bytes(AES.block_size)
	iv = get_random_bytes(AES.block_size)
	return key, iv


# AES Encryption/Decryption

def encryptAES(key, iv, plaintext):
	cipher = AES.new(key, AES.MODE_CBC, iv)
	return cipher.encrypt(pad(plaintext, AES.block_size))
	
def decryptAES(key, iv, ciphertext):
	cipher = AES.new(key, AES.MODE_CBC, iv)
	return unpad(cipher.decrypt(ciphertext), AES.block_size)


# RSA Encryption/Decryption

def encryptRSA(key, plaintext):
    cipher = PKCS1_OAEP.new(key)
    return cipher.encrypt(plaintext)

def decryptRSA(key, ciphertext):
    cipher = PKCS1_OAEP.new(key)
    return cipher.decrypt(ciphertext)


# Registration and Login

def get_password_hash(password):
    return sha256(password).hexdigest()

def generate_salt():
    return bcrypt.gensalt()

def hash_with_salt(salt, data):
    return bcrypt.hashpw(data, salt)

def verify_hash(salt, data, hsh):
    return hsh == bcrypt.hashpw(data, salt)

def hash_password_with_salt(salt, password):
    return hash_with_salt(salt, get_password_hash(password))


# Signatures

def sign(private_key, data):
    return encryptRSA(private_key, sha256(data).digest())

def verify_signature(public_key, data, signature):
    return decryptRSA(public_key, signature) == sha256(data).digest()
