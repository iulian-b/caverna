import os
import sys
import argparse

from utils import db_tools, pwd_tools
import ui.login
import ui.vault
import ui.utils


def main():
    DEBUG = False

    parsarg = argparse.ArgumentParser(description="Description")
    parsarg.add_argument("-N", "--new", action="store_true", help="Create a new user")
    parsarg.add_argument("-C", "--change-pwd", type=str, nargs=1, help="Change Password", metavar="[USERNAME]")
    parsarg.add_argument("-v", "--version", action="store_true", help="Print version")
    parsarg.add_argument("-d", "--debug", action="store_true", help="Enable debugging")
    args = parsarg.parse_args()

    if args.debug:
        DEBUG = True

    if args.new:
        new_user = input("[Username]: ")
        new_mpwd = input("[Master Password]: ")

        try:
            f = open("caves/" + new_user + ".db", "x")
            f.close()
            if DEBUG: print(f"[DEBUG]: Created user db for {new_user}")

            new_hash = pwd_tools.pwd_gen_new_hash(new_mpwd)
            new_salt = pwd_tools.pwd_get_salt(new_hash)
            if DEBUG: print(f"[DEBUG]: Created hashed mpwd for {new_user}")
            if DEBUG: print(f"[DEBUG]: HASH: {new_hash}")
            if DEBUG: print(f"[DEBUG]: SALT: {new_salt}")

            db_tools.db_add_user(new_user, new_salt)
            if DEBUG: print(f"[DEBUG]: Added {new_user} with salt {new_salt} to _users.db")

            db_tools.db_user_initialize(new_user, new_hash)
            if DEBUG: print(f"[DEBUG]: Initialized new pwd vault {new_user}.db")
        except Exception as e:
            if os.path.exists(f'{new_user}.db'):
                print("[ERROR]: User already exists")
            else:
                print(f"[ERROR]: Could not create new user ({e})")

            sys.exit()

    if args.version:
        print(ui.utils.LOGO_ASCII)
        print(ui.utils.VERSION)
        sys.exit()


if __name__ == "__main__":
    main()

    # login = ui.login.Login()
    # res = login.run()

    # USERNAME = res[0]
    # PASSWORD = res[1]
    USERNAME = "ibocse"
    PASSWORD = "$argon2id$v=19$m=65536,t=3,p=4$i5oX1TMuyPaaoESIVRJggQ$mpnUR8llQ/fuwU8mTves4dzct2t5koaBYZ4Jb1DleRI"
    # print(USERNAME)
    # print(PASSWORD)

    vault = ui.vault.Vault(USERNAME, PASSWORD)
    vault.USERNAME = USERNAME
    vault.PASSWORD = PASSWORD
    res = vault.run()
