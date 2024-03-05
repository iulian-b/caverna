from hashlib import sha256
import hashlib


def main():
    mp = input("E:").encode()
    cp = hashlib.sha256.encode(mp).hexdigest()
    print(str(cp))


main()
