import base64

import pyscrypt
from Cryptodome.Cipher import ChaCha20_Poly1305
from argon2 import PasswordHasher

import utils.db_tools as db_tools
import utils.pwd_tools as pwd_tools


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
    inputmp = "spiruharet12d3!"
    user = "ibocse"

    input_pw = ph.hash(inputmp)
    print("INPUT  : " + input_pw)

    control_pw = db_tools.db_user_get_hash(user)
    print("CONTROL: " + control_pw)

    ph.verify(control_pw, mp)

main()
