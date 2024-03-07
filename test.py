import base64
import secrets
import sqlite3
import string
from hashlib import sha256
import hashlib

import pyscrypt
from Cryptodome.Cipher import ChaCha20_Poly1305
from pysqlcipher3 import dbapi2 as sqlite
from argon2 import PasswordHasher

import db_tools
import pwd_tools


def encrypt(pw, mstr, slt):
    header = b"header"
    pw = pw.encode('utf-8')

    # Password Key Derivation Function with master and second factor password
    key = pyscrypt.hash(mstr, slt, 8192, 8, 1, 32)

    ch = ChaCha20_Poly1305.new(key=key)
    ch.update(header)
    chpw, tag = ch.encrypt_and_digest(pw)

    # Encode results from bytes to Base64
    nonce = base64.b64encode(ch.nonce).decode('utf-8')
    header = base64.b64encode(header).decode('utf-8')
    tag = base64.b64encode(tag).decode('utf-8')
    chpw = base64.b64encode(chpw).decode('utf-8')

    # Return nonce, header, tag and encrypted password
    return nonce, header, tag, chpw


def decrypt(nonce, header, tag, chpw, mstr, slt):
    # Decode results from Base64 to bytes
    nonce = base64.b64decode(nonce.encode('utf-8'))
    header = base64.b64decode(header.encode('utf-8'))
    tag = base64.b64decode(tag.encode('utf-8'))
    chpw = base64.b64decode(chpw.encode('utf-8'))

    # Password Key Derivation Function with master and second factor password
    key = pyscrypt.hash(mstr, slt, 8192, 8, 1, 32)

    ch = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    ch.update(header)
    enpw = ch.decrypt_and_verify(chpw, tag)

    return enpw


def main():
    ph = PasswordHasher()
    mp = "spiruharet123!"
    user = "ibocse"

main()
