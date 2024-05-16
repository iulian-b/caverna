# Packages
import os
import sys
import argparse
import atexit

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from getpass import getpass

# Caverna classes
import ui.login
import ui.vault
import ui.utils
import ui.menu
from utils import db_tools, pwd_tools, sync_tools

########################################################################################################################
def main():
    # Enables verbosity
    DEBUG = False

    # Arguments
    parsarg = argparse.ArgumentParser(description="Description")
    parsarg.add_argument("-N", "--new", action="store_true", help="Create a new user")
    parsarg.add_argument("-C", "--changepwd", action="store_true", help="Change a user's master password")
    parsarg.add_argument("-v", "--version", action="store_true", help="Print version")
    parsarg.add_argument("-d", "--debug", action="store_true", help="Enable debugging")
    args = parsarg.parse_args()

    ########################################################################################################################
    # Argument --debug
    if args.debug:
        DEBUG = True

    ########################################################################################################################
    # Argument --version
    if args.version:
        print(ui.utils.LOGO_ASCII)
        print(ui.utils.VERSION_LONG)
        sys.exit()

    ########################################################################################################################
    # Argument --new
    if args.new:
        # Get username and master password
        new_user = input("[NEW] Username: ")
        new_mpwd = getpass("[NEW] Master Password: ")
        new_pepper = getpass("[NEW] Secret: ")

        try:
            # Pepper master password
            pep_mpwd = new_mpwd + new_pepper

            # Hash master password
            new_hash = pwd_tools.pwd_gen_new_hash(pep_mpwd)
            if DEBUG: print(f"[args.new] Created hashed mpwd for {new_user}")
            if DEBUG: print(f"[args.new] HASH: {new_hash}")
            if DEBUG: print(f"[args.new] Added {new_user} with mpwd {new_hash} to _users.db")

            # Add username and hashed mpwd to _users database
            db_tools.db_add_user(new_user, new_hash)

            # Create new temp database file for user
            f = open("caves/" + new_user + "_temp.db", "x")
            f.close()
            if DEBUG: print(f"[args.new] Created user db({new_user}_temp) for {new_user}")

            # Setup user database schema
            db_tools.db_user_initialize(new_user, new_hash)
            if DEBUG: print(f"[args.new] Initialized new pwd vault {new_user}.db")

            # Split database file
            db_tools.db_user_split_db(f"caves/{new_user}_temp.db", new_user, new_pepper)
            print(f"[NEW] Split {new_user}_temp.db into smaller chunks")

            # Remove temp database file
            os.remove(f"caves/{new_user}_temp.db")
            if DEBUG: print(f"[args.new] Removed {new_user}_temp.db")
            print(f"[NEW] Successfully created new vault for user {new_user}")
            print(f"[NEW] Start caverna with \"python3 .caverna.py\" to login")

        except Exception as e:
            # Exception if the user database file already exists
            if os.path.exists(f'{new_user}.db'):
                print("[args.new] User already exists")
            else:
                print(f"[args.new] Could not create new user: ({e})")
            os.remove(f"{new_user}_temp.db")

        sys.exit()

    ########################################################################################################################
    # Argument --change-pwd
    if args.changepwd:
        # Get username and master password
        change_username = input(f"[CHANGE PWD] Username: ")
        old_mpwd = getpass(f"[CHANGE PWD] User {change_username} master password: ")
        pepper = getpass(f"[CHANGE PWD] User {change_username} secret: ")
        if DEBUG: print(f"[args.changepwd] Got old mpwd {old_mpwd} and pepper {pepper} by user {change_username}")

        # Hash the username + pepper + 0 (first file in split-file chain)
        change_username_hashed = sync_tools.sync_hash_user(change_username + pepper + "0")

        # Check if first file in chain exists, exit if it doesn't
        # This method prevents unknown users from finding out which other usernames are valid or not
        if not os.path.isfile("caves/" + change_username_hashed + ".cvrn"):
            print("[CHANGE PWD] Incorrect credentials")
            sys.exit()

        new_hash = ""
        control_hash = ""
        OLD_PASSWORDS_E = []
        OLD_NONCES = []
        OLD_PASSWORDS_D = []

        # Update the database containing the users and mpwd hashes
        try:
            # Get the old mpwd hash
            ph = PasswordHasher()
            control_hash = db_tools.db_user_get_hash(change_username)
            if DEBUG: print(f"[args.changepwd] Hash from old password: {control_hash}")

            # Check if the inputted mpwd is correct with the hash
            ph.verify(control_hash, old_mpwd)
            if DEBUG: print(f"[args.changepwd] Argon2 verification OK")

            # Create a new hash for the new master password
            new_mpwd = input("[CHANGE PWD] New master password: ")
            new_hash = ph.hash(new_mpwd)
            if DEBUG: print(f"[args.changepwd] Hashed new password: {new_hash}")

            # Connect to the users database
            conn = db_tools.db_stash_connect()
            if DEBUG: print(f"[args.changepwd] Connected to users db")
            c = conn.cursor()

            # Change the old mpwd hash with the new one
            c.execute(db_tools.sql_stash("update_user", (str(change_username), new_hash)))
            if DEBUG: print(
                f"[args.changepwd] Executed query: {db_tools.sql_stash('update_user', (str(change_username), new_hash))}")

            # Close the connection
            conn.commit()
            conn.close()
            if DEBUG: print(f"[args.changepwd] Terminated connection with db")

        # Argon2 hash mismatch (invalid password)
        except VerifyMismatchError:
            print("[CHANGE PWD]: FAILED (incorrect master password)")

        # Update the user's vault database
        try:
            # Join user's database
            if os.path.exists(f"caves/{change_username}.cvrn"):
                os.remove(f"caves/{change_username}.cvrn")

            db_tools.db_user_join_splits(change_username, pepper)
            if DEBUG: print(f"[args.changepwd] Retrieved {change_username}.cvrn database")

            # Connect to the user's database
            conn = db_tools.db_user_connect(change_username, pepper, control_hash)
            c = conn.cursor()
            if DEBUG: print(f"[args.changepwd] Connected to db")

            # Get all of the encrypted passwords and their nonces
            c.execute(db_tools.sql("select_all_paswd_crypto", ""))
            res = c.fetchall()
            if DEBUG: print(
                f"[args.changepwd] Executed query: {db_tools.sql('select_all_paswd_crypto', '')}")

            # Get the old key from the old mpwd hash
            old_key = pwd_tools.pwd_encrypt_key(control_hash)
            if DEBUG: print(f"[args.changepwd] encrypted old key({old_key.decode('ISO-8859-1')})")

            # Create the new key from the new mpwd hash
            new_key = pwd_tools.pwd_encrypt_key(new_hash)
            if DEBUG: print(f"[args.changepwd] encrypted new key({new_key.decode('ISO-8859-1')})")

            # Traverse the query results
            for row in res:
                old_ciphertext = row[0]
                old_nonce = row[1]
                if DEBUG: print(f"[args.changepwd] ROW: {old_ciphertext}, {old_nonce}")

                # Store the old encrypted passwords and nonces
                OLD_PASSWORDS_E.append(old_ciphertext)
                OLD_NONCES.append(old_nonce)

                # Decrypt the passwords and store them
                old_password = pwd_tools.pwd_decrypt(old_ciphertext, old_nonce, old_key)
                OLD_PASSWORDS_D.append(old_password)
                if DEBUG: print(f"[args.changepwd] decrypted password {old_ciphertext} -> {old_password}")

            # Traverse the query results again
            # This could be improved, but it works and its fragile spaghetti code
            for i in range(len(OLD_PASSWORDS_D)):
                # Re-encrypt the unencrypted passwords with the new key and new nonce
                new_ciphertext, new_nonce = pwd_tools.pwd_encrypt(OLD_PASSWORDS_D[i], new_key)
                if DEBUG: print(
                    f"[args.changepwd] encypted old password with new key {OLD_PASSWORDS_D[i]} -> {new_ciphertext} new nonce: {new_nonce}")

                # Update the old encrypted password and nonces in the user's db with the new ones
                c.execute(db_tools.sql("update_crypto", (new_ciphertext, new_nonce, OLD_PASSWORDS_E[i], OLD_NONCES[i])))
                if DEBUG: print(
                    f"[args.changepwd] Executed query: {db_tools.sql('update_crypto', (new_ciphertext, new_nonce, OLD_PASSWORDS_E[i], OLD_NONCES[i]))}")
                if DEBUG: print(
                    f"[args.changepwd] Updated old encrypted pw({OLD_PASSWORDS_E[i]} -> {new_ciphertext}) and nonce({OLD_NONCES[i]} -> {new_nonce})")

            # Rekey the sqlcipher database
            c.execute(f"""PRAGMA rekey='{new_hash}'""")
            if DEBUG: print(f"[args.changepwd] rekeyd db with new mpwd({new_hash})")

            # Close the connection
            conn.commit()
            conn.close()
            if DEBUG: print(f"[args.changepwd] Terminated connection with db")

            # Get re-keyed database joint file
            # new_temp_db = db_tools.db_user_join_splits(change_username, pepper)

            # Remove old split files
            db_tools.db_user_remove_splits(change_username, pepper)
            if DEBUG: print(f"[args.changepwd] Removed old 4 .cvrn files")

            # Re-split new database file
            db_tools.db_user_join_splits(change_username, pepper)
            if DEBUG: print(f"[args.changepwd] Split new joint .cvrn")

            # Delete joint database file
            os.remove(f"caves/{change_username}.cvrn")
            if DEBUG: print(f"[args.changepwd] Removed joint .cvrn database")

            print("[CHANGE PWD] New master password successfully set")

        except Exception as e:
            print(e)

        sys.exit()

    ########################################################################################################################
    # Start the Login Textual App
    if DEBUG: print(f"[login()] Starting login")
    ui_login = ui.login.Login()
    login_res = ui_login.run()
    ui_login.exit()

    # Get the inputted username and master password
    if login_res[0] is not None:
        USERNAME = login_res[0]
        PASSWORD = login_res[1]
        SECRET = login_res[2]
    else:
        if DEBUG: print(f"[ui_login()] Minor Exception: Finished executing with None")
    if DEBUG: print(f"[ui_login()] Finished executing login with results: {USERNAME}, {PASSWORD}, {SECRET}")

    # Safe remove user database before initializing vault
    userpath = f"caves/{USERNAME}.cvrn"
    if os.path.exists(userpath):
        os.remove(userpath)

    # Join fragments into user database
    db_tools.db_user_join_splits(USERNAME, SECRET)

    # Start the Menu Textual App
    ui_menu = ui.menu.Menu(USERNAME, PASSWORD, SECRET, DEBUG)
    menu_res = ui_menu.run()
    ui_menu.exit()

    # If exited correctly
    if menu_res == 0:
        if os.path.exists(userpath):
            os.remove(userpath)
        if DEBUG: print(f"[ui_menu()] Deleted {USERNAME} database")


########################################################################################################################
if __name__ == "__main__":
    main()
