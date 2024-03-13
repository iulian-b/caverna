# Packages
import string
import secrets
from base64 import b64decode, b64encode, decodebytes
from Cryptodome.Cipher import ChaCha20
from Cryptodome.Random import get_random_bytes
from argon2 import PasswordHasher


########################################################################################################################
# Generates a new argon2 hash from a given password
# Arguments:
#  - str(pwd): the password to hash
# Returns:
#  - str(new_hash)
def pwd_gen_new_hash(pwd):
    # Create an argon2 password hasher
    ph = PasswordHasher()

    # Hash the given password with random salt
    new_hash = ph.hash(password=pwd)

    # Return the hash
    return new_hash


########################################################################################################################
# Generates an encryption key from a given master password
# Arguments:
#  - str(mpwd): the master password
# Returns:
#  - bytes(mpwd)
def pwd_encrypt_key(mpwd):
    # Return the last 32 characters of the given master password as a byte-string, encoded in ISO-8859-1
    return bytes(mpwd[-32:], 'ISO-8859-1')


########################################################################################################################
# Encrypt a given text string (usually password) with a given key using XChaCha20
# Arguments:
#  - str(plaintext): the text to encrypt
#  - bytes(key): the key
# Returns:
#  - bytes(ciphertext)
#  - bytes(nonce
def pwd_encrypt(plaintext, key):
    try:
        # Encode the given plaintext in ISO-8859-1
        plaintext = plaintext.encode('ISO-8859-1')

        # Create a new XChaCha20 cipher with the given key and a random nonce.
        # For RFC7539 compliance, a byte-string of random os.bytes gets used as the nonce
        cipher = ChaCha20.new(key=key, nonce=get_random_bytes(24))

        # Encrypt the given plaintext
        ciphertext = cipher.encrypt(plaintext)

        # Retrieve and encode in base64 the nonce and ciphertext
        nonce = b64encode(cipher.nonce).decode('ISO-8859-1')
        ciphertext = b64encode(ciphertext).decode('ISO-8859-1')

        # Return the ciphertext and nonce
        return ciphertext, nonce

    # Exception if the values, types, or encodings used in the cipher are incorrect
    except ValueError as e:
        print("Value Error")
        print(e)


########################################################################################################################
# Decrypts a given XChaCha20 ciphertext by using the given nonce and key
# Arguments:
#  - bytes(ciphertext): the encrypted byte-string
#  - bytes(nonce): the nonce
#  - bytes(key): the key
# Returns:
#  - str(plaintext)
def pwd_decrypt(ciphertext, nonce, key):
    try:
        # Decode the given nonce and ciphertext from base64
        nonce = b64decode(nonce)
        ciphertext = b64decode(ciphertext)

        # Crate a new XChaCha20 cipher with the given key and decoded nonce
        cipher = ChaCha20.new(key=key, nonce=nonce)

        # Decrypt the ciphertext
        plaintext = cipher.decrypt(ciphertext)

        # Return the unencrypted plaintext
        return plaintext.decode('utf-8')

    # Exception if the values, types, or encodings used in the cipher are incorrect
    except ValueError as e:
        print("[ERROR] Decryption failure: Value Error")
        print(e)

    # Exception if the given key does not unencrypt the given ciphertext
    except KeyError as e:
        print("[ERROR] Decryption failure: Key Error")
        print(e)


########################################################################################################################
# DEPRECATED
# Generates a hash of the given password using the given salt
# def pwd_get_hash(pwd, salt):
#     ph = PasswordHasher()
#     new_hash = ph.hash(password=pwd, salt=salt)
#     return new_hash


########################################################################################################################
# DEPRECATED
# Retrieves a user's salt from a given master password hash
# def pwd_get_salt(arghash):
#     return arghash[31:53]


########################################################################################################################
# Generates a random password of a given length
# Arguments:
#  - int(size): the length
# Returns:
#  - str(pwd)
def pwd_gen(size):
    # Characters used for generation are:
    # Alpha (A-Z, a-z)
    # Numeric (0-9)
    # US Keyboard Special Characters (`~!@#$%^&*()-_=+[{]};:,<.>/?| )
    # (excluded ' and " characters, as they could mess with other functions, especially the SQL ones)
    alpha = string.ascii_letters + string.digits + '`~!@#$%^&*()-_=+[{]};:,<.>/?| '

    # Generate random characters for the given size
    pwd = ''.join(secrets.choice(alpha) for i in range(size))

    # Return the generated password
    return pwd

########################################################################################################################
# DEPRECATED
# Better way of decodint base64 for argon2 functions, avoids padding errors
# def pwd_argon_b64decode(b64str):
#     padding = "=" * (-len(b64str) % 4)
#     return decodebytes(f"{b64str}{padding}".encode("ascii"))
