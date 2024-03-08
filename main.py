import getpass
import hashlib
import os
import sys
import argparse

import pwd_tools
import db_tools

LOGO_L1 = " ██████╗ █████╗ ██╗   ██╗███████╗██████╗ ███╗   ██╗ █████╗\n"
LOGO_L2 = "██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗████╗  ██║██╔══██╗\n"
LOGO_L3 = "██║     ███████║██║   ██║█████╗  ██████╔╝██╔██╗ ██║███████║\n"
LOGO_L4 = "██║     ██╔══██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██║╚██╗██║██╔══██║\n"
LOGO_L5 = "╚██████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║██║ ╚████║██║  ██║\n"
LOGO_L6 = " ╚═════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝"
LOGO_ASCII = LOGO_L1 + LOGO_L2 + LOGO_L3 + LOGO_L4 + LOGO_L5 + LOGO_L6

VERSION = 'Caverna - 0.1a - 2024.7.3 - iulian(iulian@firemail.cc)'


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
        except:
            if os.path.exists(f'{new_user}.db'):
                print("[ERROR]: User already exists")
            else:
                print("[ERROR]: Could not create new user")

            sys.exit()

    if args.version:
        print(LOGO_ASCII)
        print(VERSION)
        sys.exit()


if __name__ == "__main__":
    main()
