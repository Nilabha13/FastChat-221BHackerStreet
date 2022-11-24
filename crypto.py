import bcrypt
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from hashlib import sha256
from utilities import *


# RSA Key Handling

def gen_RSA_keys():
    """Generates an RSA public-key private-key pair. Returns the public key and the private key.

    :rtype: Crypto.PublicKey.RSA.RsaKey, Crypto.PublicKey.RSA.RsaKey
    """
    keys = RSA.generate(2048)
    return keys.public_key(), keys

def export_key(key, filename):
    """Exports an RsaKey object to a file in the PEM format.

    :param key: The RsaKey object to be exported
    :type key: Crypto.PublicKey.RSA.RsaKey
    :param filename: The filename of the file in which the RsaKey is to be saved
    :type filename: str
    """
    keyfile = open(filename, 'wb')
    keyfile.write(key.export_key('PEM'))
    keyfile.close()

def import_key(filename):
    """Imports an RsaKey object from a file in the PEM format.

    :param filename: The filename of the file from which the RsaKey is to be imported
    :type filename: str
    :return: The RsaKey object being imported
    :rtype: Crypto.PublicKey.RSA.RsaKey
    """
    keyfile = open(filename, 'r')
    key = RSA.import_key(keyfile.read())
    keyfile.close()
    return key

def key_to_str(key):
    """Converts an RsaKey object to a string in the PEM format.

    :param key: The RsaKey object to be converted
    :type key: Crypto.PublicKey.RSA.RsaKey
    :return: The RsaKey object represented as a string
    :rtype: str
    """
    return key.export_key('PEM').decode()

def str_to_key(data):
    """Converts a string in the PEM format to an RsaKey object

    :param data: The string representation of the RsaKey object
    :type data: str
    :return: The RsaKey object represented by the string
    :rtype: Crypto.PublicKey.RSA.RsaKey
    """
    return RSA.import_key(data.encode())


# AES Key Handling

def gen_AES_key_iv():
    """Generates an AES key and IV.

    :return: The generated AES key and IV
    :rtype: bytes, bytes
    """
    key = get_random_bytes(AES.block_size)
    iv = get_random_bytes(AES.block_size)
    return key, iv


# AES Encryption/Decryption

def encryptAES(key, iv, plaintext):
    """Returns the AES encrpytion of the plaintext under CBC mode of operation with the supplied key and IV.

    :param key: The AES key
    :type key: bytes
    :param iv: The AES IV
    :type iv: bytes
    :param plaintext: The plaintext to be encrypted
    :type plaintext: bytes
    :return: The ciphertext produced by encrypting the plaintext
    :rtype: bytes
    """
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(plaintext, AES.block_size))
	
def decryptAES(key, iv, ciphertext):
    """Returns the AES decryption of the ciphertext under CBC mode of operation with the supplied key and IV.

    :param key: The AES key
    :type key: bytes
    :param iv: The AES IV
    :type iv: bytes
    :param ciphertext: The ciphertext to be decrypted
    :type ciphertext: bytes
    :return: The plaintext produced by decrypting the ciphertext
    :rtype: bytes
    """
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)


# RSA Encryption/Decryption

PT_CHUNK_SIZE = 214
def encryptRSA(key, plaintext):
    """Encrypts the plaintext using the PKCS1_OAEP standard with the supplied key

    :param key: The RSA key
    :type key: Crypto.PublicKey.RSA.RsaKey
    :param plaintext: The plaintext to be encrypted
    :type plaintext: bytes
    :return: The ciphertext produced by encrypting the plaintext
    :rtype: bytes
    """
    cipher = PKCS1_OAEP.new(key)
    pt_chunks = [plaintext[i:i+PT_CHUNK_SIZE] for i in range(0, len(plaintext), PT_CHUNK_SIZE)]
    return b''.join([cipher.encrypt(pt_chunk) for pt_chunk in pt_chunks])

CT_CHUNK_SIZE = 256
def decryptRSA(key, ciphertext):
    """Decrypts the ciphertext using the PKCS1_OAEP standard with the supplied key

    :param key: The RSA key
    :type key: Crypto.PublicKey.RSA.RsaKey
    :param ciphertext: The ciphertext to be decrypted
    :type ciphertext: bytes
    :return: The plaintext produces by decrypting the ciphertext
    :rtype: bytes
    """
    cipher = PKCS1_OAEP.new(key)
    ct_chunks = [ciphertext[i:i+CT_CHUNK_SIZE] for i in range(0, len(ciphertext), CT_CHUNK_SIZE)]
    return b''.join([cipher.decrypt(ct_chunk) for ct_chunk in ct_chunks])


# Registration and Login

def generate_salt():
    """Generates a salt for the bcrypt hash function

    :return: The generated salt
    :rtype: bytes
    """
    return bcrypt.gensalt()

def hash_with_salt(salt, data):
    """Computes the salted hash using bcrypt of the supplied data with the supplied salt

    :param salt: The salt
    :type salt: bytes
    :param data: The data whose salted hash is to be computed
    :type data: bytes
    :return: The salted hash
    :rtype: bytes
    """
    return bcrypt.hashpw(data, salt)

def verify_hash(salt, data, hsh):
    """Verifies whether the supplied hash is equal to the salted hash using bcrypt of the supplied data with the supplied salt

    :param salt: The salt
    :type salt: bytes
    :param data: The data whose salted hash is computed
    :type data: bytes
    :param hsh: The hash whose value needs to be compared with that of the computed salted hash
    :type hsh: bytes
    :return: Whether the supplied hash is equal to the computed salted hash
    :rtype: bool
    """
    return hsh == bcrypt.hashpw(data, salt)


# Signatures

def sign(private_key, data):
    """Signs the supplied data using the supplied private key

    :param private_key: The private signing key of the signer
    :type private_key: Crypto.PublicKey.RSA.RsaKey
    :param data: The data to sign
    :type data: bytes
    :return: The required digital signature
    :rtype: bytes
    """
    return encryptRSA(private_key, sha256(data).digest())

def verify_signature(public_key, data, signature):
    """Verifies the digital signature on the supplied data given the required public key

    :param public_key: The public verification key of the signer
    :type public_key: Crypto.PublicKey.RSA.RsaKey
    :param data: The data whose signature has to be verified
    :type data: bytes
    :param signature: The digital signature
    :type signature: bytes
    :return: Whether the digital signature on the data successfully verifies
    :rtype: bool
    """
    return decryptRSA(public_key, signature) == sha256(data).digest()
