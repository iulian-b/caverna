import base64

import pyscrypt
from Cryptodome.Cipher import ChaCha20_Poly1305
from argon2 import PasswordHasher
from Cryptodome.Random import get_random_bytes

import utils.db_tools as db_tools
import utils.pwd_tools as pwd_tools

def main():
    pw = "test123"
    key = "uwU8mTves4dzct2t5koaBYZ4Jb1DleRI"
    enckey = bytes(key, 'utf-8')

    decod = enckey.decode('utf-8')
    print("KEY: " + decod)
    ciphertext, nonce = pwd_tools.pwd_encrypt(pw, enckey)
    dec = pwd_tools.pwd_decrypt(ciphertext, nonce, enckey)
    print(dec)

    u = "$argon2id$v=19$m=65536,t=3,p=4$aHPSD8Bd19DCsJ0ongr6Sg$t4UBUtIyorrRyjPHhPpNNiYPjvuqiABkcqKZTTcL1Vo"
    print("RyjPHhPpNNiYPjvuqiABkcqKZTTcL1Vo")
    print(u)
    print(u[-32:])
main()
