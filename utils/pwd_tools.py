from base64 import b64decode, b64encode, decodebytes
import string
import secrets
from Cryptodome.Cipher import ChaCha20
from Cryptodome.Random import get_random_bytes
from argon2 import PasswordHasher


def pwd_gen_new_hash(pwd):
    ph = PasswordHasher()
    new_hash = ph.hash(password=pwd)
    return new_hash


def pwd_encrypt_key(mpwd):
    return bytes(mpwd[-32:], 'utf-8')


def pwd_encrypt(pwd, key):
    pwd = pwd.encode()
    # rfc7539
    cipher = ChaCha20.new(key=key, nonce=get_random_bytes(24))
    ciphertext = cipher.encrypt(pwd)
    nonce = b64encode(cipher.nonce).decode('utf-8')
    ciphertext = b64encode(ciphertext).decode('utf-8')
    return ciphertext, nonce


def pwd_decrypt(ciphertext, nonce, key):
    try:
        nonce = b64decode(nonce)
        ciphertext = b64decode(ciphertext)

        cipher = ChaCha20.new(key=key, nonce=nonce)
        plaintext = cipher.decrypt(ciphertext)
        return plaintext.decode()

    except ValueError as e:
        print("Value Error")
        print(e)
    except KeyError as e:
        print("Key Error")
        print(e)


def pwd_get_hash(pwd, salt):
    ph = PasswordHasher()
    new_hash = ph.hash(password=pwd, salt=salt)
    return new_hash


# DEPRECATED
# def pwd_get_salt(arghash):
#     return arghash[31:53]


def pwd_gen(size):
    alpha = string.ascii_letters + string.digits + '`~!@#$%^&*()-_=+[{]};:,<.>/?| '
    pwd = ''.join(secrets.choice(alpha) for i in range(size))
    return pwd


def pwd_argon_b64decode(b64str):
    padding = "=" * (-len(b64str) % 4)
    return decodebytes(f"{b64str}{padding}".encode("ascii"))
