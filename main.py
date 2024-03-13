import os
import sys
import argparse

import argon2

from utils import db_tools, pwd_tools
import ui.login
import ui.vault
import ui.utils


def main():
    DEBUG = False

    parsarg = argparse.ArgumentParser(description="Description")
    parsarg.add_argument("-N", "--new", action="store_true", help="Create a new user")
    parsarg.add_argument("-C", "--changepwd", type=str, nargs=1, help="Change Password", metavar="[USERNAME]")
    parsarg.add_argument("-v", "--version", action="store_true", help="Print version")
    parsarg.add_argument("-d", "--debug", action="store_true", help="Enable debugging")
    args = parsarg.parse_args()

    # --debug
    if args.debug:
        DEBUG = True

    # --version
    if args.version:
        print(ui.utils.LOGO_ASCII)
        print(ui.utils.VERSION)
        sys.exit()

    # --new
    if args.new:
        new_user = input("[NEW] Username: ")
        new_mpwd = input("[NEW] Master Password: ")

        try:
            new_hash = pwd_tools.pwd_gen_new_hash(new_mpwd)
            if DEBUG: print(f"[args.new] Created hashed mpwd for {new_user}")
            if DEBUG: print(f"[args.new] HASH: {new_hash}")

            db_tools.db_add_user(new_user, new_hash)
            if DEBUG: print(f"[args.new] Added {new_user} with mpwd {new_hash} to _users.db")

            f = open("caves/" + new_user + ".db", "x")
            f.close()
            if DEBUG: print(f"[args.new] Created user db for {new_user}")

            db_tools.db_user_initialize(new_user, new_hash)
            if DEBUG: print(f"[args.new] Initialized new pwd vault {new_user}.db")

            print(f"[NEW] Successfully created new vault for user {new_user}")
            print(f"[NEW] Start caverna with \"python3 .caverna.py\" to login")

        except Exception as e:
            if os.path.exists(f'{new_user}.db'):
                print("[args.new] User already exists")
            else:
                print(f"[args.new] Could not create new user ({e})")

        sys.exit()

    # --change-pwd
    if args.changepwd:
        print(f"[CHANGE PWD] Changing password for {args.changepwd[0]}")
        old_mpwd = input(f"[CHANGE PWD] User {args.changepwd[0]} master password: ")
        if DEBUG: print(f"[args.changepwd] Got old mpwd {old_mpwd} by user {args.changepwd[0]}")

        try:
            # Check input validity
            ph = argon2.PasswordHasher()
            control_hash = db_tools.db_user_get_hash(args.changepwd[0])
            if DEBUG: print(f"[args.changepwd] Hash from old password: {control_hash}")
            ph.verify(control_hash, old_mpwd)
            if DEBUG: print(f"[args.changepwd] Argon2 verification OK")

            # New master password hash
            new_mpwd = input("[CHANGE PWD] New master password: ")
            new_hash = ph.hash(new_mpwd)
            if DEBUG: print(f"[args.changepwd] Hashed new password: {new_hash}")

            # Update users db
            conn = db_tools.db_stash_connect()
            if DEBUG: print(f"[args.changepwd] Connected to users db")
            c = conn.cursor()
            c.execute(db_tools.sql("update_user", (str(args.changepwd[0]), new_mpwd)))
            if DEBUG: print(f"[args.changepwd] Executed query: {db_tools.sql('update_user', (str(args.changepwd[0]), new_mpwd))}")
            conn.commit()
            conn.close()
            if DEBUG: print(f"[args.changepwd] Terminated connection with db")
            print("[CHANGE PWD] New master password successfully set")

        # Argon2 hash mismatch (invalid password)
        except argon2.exceptions.VerifyMismatchError:
            print("[CHANGE PWD]: FAILED (incorrect master password)")

        sys.exit()


    ### UI START
    # Login
    # if DEBUG: print(f"[login()] Starting login")
    # login = ui.login.Login()
    # res = login.run()
    #
    # USERNAME = res[0]
    # PASSWORD = res[1]
    # if DEBUG: print(f"[login()] Finished executing login with results: {USERNAME}, {PASSWORD}")

    #USERNAME = "ibocse"
    #PASSWORD = "$argon2id$v=19$m=65536,t=3,p=4$i5oX1TMuyPaaoESIVRJggQ$mpnUR8llQ/fuwU8mTves4dzct2t5koaBYZ4Jb1DleRI"

    USERNAME = "bob"
    PASSWORD = "$argon2id$v=19$m=65536,t=3,p=4$VanZOqKDAUIe//ehTKKC6w$XzwXeJ8RoOzMTXoeQ21dv+dGmicLXjoltthm+BiaCjM"

    # Vault
    if DEBUG: print(f"[vault(USERNAME, PASSWORD, DEBUG)] Starting vault with arguments: {USERNAME}, {PASSWORD}, {DEBUG}")
    vault = ui.vault.Vault(USERNAME, PASSWORD, DEBUG)
    vault.USERNAME = USERNAME
    vault.PASSWORD = PASSWORD
    vault.run()
    if DEBUG: print(f"[vault(USERNAME, PASSWORD, DEBUG)] Finished executing vault")


if __name__ == "__main__":
    main()
