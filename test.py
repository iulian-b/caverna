import base64

import pyscrypt
from Cryptodome.Cipher import ChaCha20_Poly1305, ChaCha20
from argon2 import PasswordHasher
from Cryptodome.Random import get_random_bytes

import utils.db_tools as db_tools
import utils.pwd_tools as pwd_tools


def main():
    key = pwd_tools.pwd_encrypt_key("$argon2id$v=19$m=65536,t=3,p=4$CCJi41xNxq5iEnSkgLQaeQ$vhb2bOu9HrGOtJwqARmtee6UD77JA9DSK/iTgu3lEOE")
    pw1 = base64.b64decode("ZJq+NXxM")
    nonce1 = base64.b64decode("37qiI7As7WqXW5sCu6xmpCnUs0o5Ow/S")

    pw2 = "helloboss"
    # pw2 = pw2.encode('latin-1')
    # cipher = ChaCha20.new(key=key, nonce=nonce)
    # ct = cipher.encrypt(pw2)
    # print(ct.decode('latin-1'))

    cipher = ChaCha20.new(key=key, nonce=nonce1)
    plaintext = cipher.decrypt(pw1)
    print(plaintext.decode('ISO-8859-1'))
    print(plaintext)


    # str = "ÎågS"ISO-8859-1
    # print(str.encode('latin-1'))
    # print(str.encode('ISO-8859-1'))
    # print(str.encode('utf-8'))

    # nonce = base64.b64decode(nonce)
    # ciphertext = base64.b64decode(pw)

    # cipher = ChaCha20.new(key=key, nonce=nonce)
    # plaintext = cipher.decrypt(pw)
    # print("The message was " + str(plaintext))

    # nonce = base64.b64encode(cipher.nonce).decode('utf-8')
    # ct = base64.b64encode(ciphertext).decode('utf-8')

    # print(nonce)
    # print(ct)

    # nonce = 'r7pTwMy+px8uc9w+dASR9hX5zEpvh19v'
    # key = 'Gw2eKyejNpxxK9AcKl7Ws5dklGH8+Z4w'
    #
    # plain = pwd_tools.pwd_decrypt(pw, nonce, key)
    #
    # print(plain)
    # ciphertext, nonce = pwd_tools.pwd_encrypt(pw, enckey)
    # dec = pwd_tools.pwd_decrypt(pw, nonce, key)
    # print(dec)


main()
