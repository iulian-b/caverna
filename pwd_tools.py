import base64
import os
import hashlib
import random
import string
import time
import secrets

import pyscrypt
from pbkdf2 import PBKDF2
from Cryptodome.Cipher import AES
from getpass import getpass
from argon2 import PasswordHasher
from base64 import b64encode, b64decode
from Cryptodome.Cipher import ChaCha20_Poly1305


def pwd_gen_new_hash(pwd):
    ph = PasswordHasher()
    new_hash = ph.hash(password=pwd)
    return new_hash


def pwd_get_hash(pwd, salt):
    ph = PasswordHasher()
    new_hash = ph.hash(password=pwd, salt=salt)
    return new_hash


def pwd_get_salt(arghash):
    return arghash[31:53]


def pwd_gen(size):
    alpha = string.ascii_letters + string.digits + '-_!@#$%^&*()`~[{]};:'",<.>?"
    pwd = ''.join(secrets.choice(alpha) for i in range(size))
    return pwd_gen_new_hash(pwd)


def pwd_b64decode(b64str):
    padding = "=" * (-len(b64str) % 4)
    return base64.decodebytes(f"{b64str}{padding}".encode("ascii"))
