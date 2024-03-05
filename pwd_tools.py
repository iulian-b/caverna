import os
import hashlib
import string
import secrets
from pbkdf2 import PBKDF2
from Cryptodome.Cipher import AES
from base64 import b64encode, b64decode

salt = os.urandom(32)


def pwd_gen(size):
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(size))


def mpwd_gen():
    # mpwd = input("Enter your Master Password").encode()
    mpwd = "spiruharet123!".encode()
    tmp = hashlib.sha256(mpwd).hexdigest()
    print("Master Password: " + str(tmp))


def mpwd_query(mpwd, twofa):
    #spriharet123!
    mpwd_hash = "0b8fc4369cc4c493b44adc92d6f286640dfe5c45bbbf8f3181953d6e09565c0d"
    if hashlib.sha256(mpwd + twofa).hexdigest() == mpwd_hash:
        return True


def encrypt(pwd, mpwd_hash):
    key = PBKDF2(str(mpwd_hash), salt).read(32)

    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(str.encode(pwd))
    add_nonce = ciphertext + cipher.nonce

    return b64encode(add_nonce).decode()


def decrypt(pwd, mpwd_hash):
    if len(pwd) % 4:
        pwd += '=' * (4 - len(pwd) % 4)

    key = PBKDF2(str(mpwd_hash), salt).read(32)
    nonce = b64decode(pwd)[-16:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)

    return cipher.decrypt(b64decode(pwd)[:-16])