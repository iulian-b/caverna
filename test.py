import base64
import hashlib
import os
import platform
import time
from pathlib import Path

import pyscrypt
import hmac
from Cryptodome.Cipher import ChaCha20_Poly1305, ChaCha20
from argon2 import PasswordHasher
from Cryptodome.Random import get_random_bytes

import utils.db_tools as db_tools
import utils.pwd_tools as pwd_tools
from utils import sync_tools


def main():
    # key = pwd_tools.pwd_encrypt_key("$argon2id$v=19$m=65536,t=3,p=4$CCJi41xNxq5iEnSkgLQaeQ$vhb2bOu9HrGOtJwqARmtee6UD77JA9DSK/iTgu3lEOE")
    # pw1 = base64.b64decode("ZJq+NXxM")
    # nonce1 = base64.b64decode("37qiI7As7WqXW5sCu6xmpCnUs0o5Ow/S")

    # pw2 = "helloboss"
    # pw2 = pw2.encode('latin-1')
    # cipher = ChaCha20.new(key=key, nonce=nonce)
    # ct = cipher.encrypt(pw2)
    # print(ct.decode('latin-1'))

    # cipher = ChaCha20.new(key=key, nonce=nonce1)
    # plaintext = cipher.decrypt(pw1)
    # print(plaintext.decode('ISO-8859-1'))
    # print(plaintext)

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

    #import utils.sync_tools as sync_tools
    #sync_tools.sync_check_network()
    # ph = PasswordHasher()
    # pepper = input("PEPPER = ")
    # pwd = "spiruharet123!" + pepper
    # print(pepper)
    # print(pwd)
    #
    # # Hash the given password with random salt
    # h1 = ph.hash(password=pwd)
    # print(h1)
    #
    # inp = input("PASS= ")
    # ph.verify(h1, inp)

    # u1 = "caves/" + sync_tools.sync_hash_user("03906b7d983bdebd8df7d7697bdbc4ba1fa710130b36cd406dd4a523e589a896" + pepper + "1") + ".cvrn"
    # u2 = "caves/" + sync_tools.sync_hash_user("03906b7d983bdebd8df7d7697bdbc4ba1fa710130b36cd406dd4a523e589a896" + pepper + "2") + ".cvrn"
    # u3 = "caves/" + sync_tools.sync_hash_user("03906b7d983bdebd8df7d7697bdbc4ba1fa710130b36cd406dd4a523e589a896" + pepper + "3") + ".cvrn"
    # u4 = "caves/" + sync_tools.sync_hash_user("03906b7d983bdebd8df7d7697bdbc4ba1fa710130b36cd406dd4a523e589a896" + pepper + "4") + ".cvrn"

    # JOIN
    # f1 = open(u1, 'rb')
    # f2 = open(u2, 'rb')
    # f3 = open(u3, 'rb')
    # f4 = open(u4, 'rb')
    # fU = open("caves/" + username + ".cvrn", 'wb')
    #
    # fU.write(f1.read())
    # fU.write(f2.read())
    # fU.write(f3.read())
    # fU.write(f4.read())
    # fU.close()
    # f1.close()
    # f2.close()
    # f3.close()
    # f4.close()
    from tempmail import EMail

    email = EMail()
    print(email.address)  # qwerty123@1secmail.com

    # ... request some email ...

    msg = email.wait_for_message()
    print(msg.body)  # Hello World!\n



main()
