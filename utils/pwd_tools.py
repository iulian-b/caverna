import base64
import string
import secrets

from argon2 import PasswordHasher


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
