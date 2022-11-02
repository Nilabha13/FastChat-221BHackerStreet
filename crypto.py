import bcrypt
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from hashlib import sha256
import random


# Key Handling

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


# Encryption/Decryption

def encrypt(key, plaintext):
    cipher = PKCS1_OAEP.new(key)
    return cipher.encrypt(plaintext)

def decrypt(key, ciphertext):
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
    return encrypt(private_key, sha256(data).digest())

def verify_signature(public_key, data, signature):
    return decrypt(public_key, signature) == sha256(data).digest()