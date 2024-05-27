# Packages
import datetime
import os
import random

from pysqlcipher3 import dbapi2 as sqlcipher
from utils import sync_tools
from utils import pwd_tools


########################################################################################################################
# Splits a temporary .db file at a given path into 4 smaller files
# Arguments:
#  - str(tempfile_path) the path of the temp .db file
#  - str(split_filename) the hash of the username + pepper
#  - str(secret) the user's secret
def db_user_split_db(tempfile_path, user, pepper):
    # File size of the temp .db file
    FILE_SIZE = os.stat(tempfile_path).st_size

    # Fragmentation Factor
    FRAGMENTS = round(FILE_SIZE / 1024)

    # The amount of bytes to read at a time
    CHUNK_SIZE = int(FILE_SIZE / FRAGMENTS)

    # The temporary .db file
    tempfile = open(tempfile_path, 'rb')

    # Read the first chunk of data
    chunk = tempfile.read(CHUNK_SIZE)
    for i in range(FRAGMENTS):
        # Hash new split filename
        split_filename = sync_tools.sync_hash_user(user + pepper + str(i))

        # Open new split file
        split_file = open(f"caves/{split_filename}.cvrn", 'wb')

        # Write a chunk of the temp file to it
        split_file.write(chunk)

        # Close the split file
        split_file.close()

        # Read the next chunk
        chunk = tempfile.read(CHUNK_SIZE)  # read the next chunk

    # Close the temp file
    tempfile.close()


########################################################################################################################
# Joins 4 split .cvrn files into a singular .cvrn file
# Arguments:
#  - str(user) the user whose split files belong to
#  - str(secret) the user's secret
def db_user_join_splits(user, secret):
    # Create empty file
    file_joint = open(f"caves/{user}.cvrn", 'wb')

    # Counter
    counter = 0

    while (1):
        # Generate hash with the user + pepper + n
        split_filename = sync_tools.sync_hash_user(user + secret + str(counter))

        # Try to open split file
        try:
            # Open split file
            split_file = open(f"caves/{split_filename}.cvrn", 'rb')

            # Append the contents of the split file into the unified file
            file_joint.write(split_file.read())

            # Close files
            split_file.close()

            # Advance counter
            counter += 1
        except FileNotFoundError:
            break

    file_joint.close()
    # return file_joint


########################################################################################################################
# Removes the 4 split databse files of a given user
# Arguments:
#  - str(user) the user whose split files belong to
#  - str(secret) the user's secret
def db_user_remove_splits(user, secret):
    for i in range(4):
        try:
            # Generate hash with the user + pepper + n
            split_filpath = sync_tools.sync_hash_user(user + secret + i)

            # Close file
            # split_file = open(split_filpath, 'rb')
            # split_file.close()

            # Try to remove n file
            if os.path.exists(split_filpath):
                os.remove(f"caves/{split_filpath}.cvrn")
            # print(split_filpath)

        # Something bad happened here
        except Exception as e:
            print(e)


########################################################################################################################
# Deletes all of the given user's database split .cvrn files, re-split's his open temporary joint database and deletes
# the old one.
# Arguments:
#  - str(user) the user
#  - str(secret) the user's secret
def db_user_resplit(user, secret):
    # Remove database fragments
    db_user_remove_splits(user, secret)

    # Resplit database
    db_user_split_db(f"caves/{user}.cvrn", user, secret)

    # Delete old joint database
    # os.remove(f"caves/{user}.cvrn")


########################################################################################################################
# Checks if a given secret, beloging to a given user, is correct by verifying if the combined hash (uname + pepper + 0),
# corresponds with an existing file present in the /caves directory
# Arguments:
#  - str(user) the username
#  - str(secret) the user's secret
# Returns:
#  - bool(true) if the given secret is correct
#  - bool(false) if the given secret is incorrect
def db_user_check_secret(user, secret) -> bool:
    # Hash the user + pepper + 0 (first file in chain)
    username_hashed = sync_tools.sync_hash_user(user + secret + "0")

    if os.path.isfile("caves/" + username_hashed + ".cvrn"):
        return True
    else:
        return False


########################################################################################################################
# Connects a given user to its own vault database by using his master password hash as the key to decrypt the database
# Arguments:
#  - str(user) the username
#  - str(secret) the user's secret
#  - str(mpwd_hash) the user's master password hash
# Returns:
#  - sqlcipher(connection)
def db_user_connect(user, secret, mpwd_hash):
    # Connect to the user's database
    user_db = open(f"caves/{user}.cvrn")
    conn = sqlcipher.connect(user_db.name)
    c = conn.cursor()

    # Set the key to the mpwd hash
    c.execute(f"PRAGMA key='{mpwd_hash}'")

    # Legacy compatibility
    c.execute("PRAGMA cipher_compatibility = 3")

    # Close the connection
    conn.commit()
    c.close()

    # Return the connection
    return conn


########################################################################################################################
# Connects to the _users database
# Returns:
#  - sqlcipher(connection)
def db_stash_connect():
    # Connect to the database
    conn = sqlcipher.connect("caves/_users.db")
    c = conn.cursor()

    # Set the key
    c.execute("PRAGMA key='b6QF9hAgPM6tCbrSMpO+MI335ShsQEodb6fudPE'")
    c.execute("PRAGMA cipher_compatibility = 3")

    # Return the connection
    return conn


########################################################################################################################
# Initialize the given user's database schema
# Arguments:
#  - str(user): the username
#  - str(mpwd): the user's master password hash
def db_user_initialize(user, mpwd):
    # Connect to the user's vault database
    conn = sqlcipher.connect("caves/" + user + "_temp.db")
    c = conn.cursor()

    # Set the key to the mpwd hash
    c.execute(f"PRAGMA key='{mpwd}'")
    c.execute("PRAGMA cipher_compatibility = 3")

    # Exectute the CREATE TABLE query for passwords vault
    c.execute("""CREATE TABLE passwords (
	    ID INTEGER PRIMARY KEY,
   	    URL TEXT NOT NULL,
	    UNAME TEXT NOT NULL,
	    PASWD TEXT NOT NULL,
	    NONCE TEXT
    )""")
    conn.commit()

    # Exectute the CREATE TABLE query for notes vault
    c.execute("""CREATE TABLE notes (
    	    ID INTEGER PRIMARY KEY,
       	    FILENAME TEXT NOT NULL UNIQUE,
    	    CONTENT TEXT,
    	    NONCE TEXT
    )""")
    conn.commit()

    # Execute the CREATE TABLE query for the OTP vault
    c.execute("""CREATE TABLE otp (
    	    ID INTEGER PRIMARY KEY,
       	    ISSUER TEXT NOT NULL,
    	    SECRET TEXT NOT NULL,
    	    NONCE TEXT
    )""")
    conn.commit()

    # Execute the CREATE TABLE query for the Entropy vault
    c.execute("""CREATE TABLE junk (
            ID INTEGER PRIMARY KEY,
            PARAM1 TEXT,
            PARAM2 TEXT,
            PARAM3 TEXT
    )""")
    conn.commit()

    # Randomly fill entropy table
    for i in range(random.randint(1, 25)):
        param1 = pwd_tools.pwd_gen(25)
        param2 = pwd_tools.pwd_gen(25)
        param3 = pwd_tools.pwd_gen(25)

        c.execute(f"INSERT INTO junk(PARAM1, PARAM2, PARAM3) VALUES(\'{param1}\', \'{param2}\', \'{param3}\')")
        conn.commit()

    # Terminate the connection
    c.close()


########################################################################################################################
# Adds a user's name and mpwd hash to the _users database so he can login
# Arguments:
#  - str(user): the username
#  - str(mpwd_hash): the master password hash
def db_add_user(user, mpwd_hash):
    # Connect to the _users database
    conn = db_stash_connect()
    c = conn.cursor()

    # Hash the username
    username = sync_tools.sync_hash_user(user)

    # Get the current timestamp as the LAD
    timestamp = datetime.datetime.now()

    # Execute the INSERT query which adds the username and mpwd hash to the 'users' table
    c.execute(f"INSERT INTO users(USER, MPWD, LAD) VALUES(\'{username}\', \'{mpwd_hash}\', \'{timestamp}\')")

    # Terminate the connection
    conn.commit()
    c.close()


########################################################################################################################
# Retrieves the given user's master password hash from the _users database
# Arguments:
#  - str(user): the username
# Returns:
#  - str(mpwd_hash)
def db_user_get_hash(user):
    # Connect to the _users database
    conn = db_stash_connect()
    c = conn.cursor()

    # Hash the username
    username = sync_tools.sync_hash_user(user)

    # Execute the SELECT query which returns the user's mpwd hash
    c.execute(f"SELECT MPWD FROM users WHERE USER = '{username}'")
    mpwd_hash = c.fetchone()

    # Return the hash
    return mpwd_hash[0]



########################################################################################################################
# A collection of commonly used sql queries
# Arguments:
#  - str(query): the name of the query
#  - str[args]: the list of arguments to be inserted into the chosen query. None can also be given.
# Returns:
#  - str(query)
def sql_pwd(query, args):
    match query:
        # [SELECT QUERIES]
        # SELECT a specific row from the vault
        case "select":
            return f"SELECT * FROM passwords WHERE URL = \'{args[0]}\' AND UNAME = \'{args[1]}\' AND PASWD = \'{args[2]}'"
        # SELECT every row from the vault
        case "print":
            return "SELECT URL, UNAME, PASWD FROM passwords"
        # SELECT only the nonce from the vault
        case "select_nonce":
            return f"SELECT NONCE FROM passwords WHERE UNAME = \'{args[0]}\' AND PASWD = \'{args[1]}\'"
        # SELECT only the encrypted password from the vault
        case "select_paswd":
            return f"SELECT PASWD FROM passwords WHERE URL = \'{args[0]}\' AND UNAME = \'{args[1]}\'"
        # SELECT all encrypted passwords and nonces from the vault
        case "select_all_paswd_crypto":
            return f"SELECT PASWD, NONCE FROM passwords"

        # [UPDATE QUERIES]
        # UPDATE a row from the vault
        case "update_row":
            return f"UPDATE passwords SET URL = \'{args[0]}\', UNAME = \'{args[1]}\', PASWD = \'{args[2]}\', NONCE = \'{args[3]}\' WHERE URL = \'{args[4]}\' AND UNAME = \'{args[5]}\' AND PASWD = \'{args[6]}\'"
        # UPDATE the encrypted password and nonce from the vault
        case "update_crypto":
            return f"UPDATE passwords SET PASWD = \'{args[0]}\', NONCE = \'{args[1]}\' WHERE PASWD = \'{args[2]}\' AND NONCE = \'{args[3]}\'"

        # [INSERT QUERIES]
        # INSERT a new row into the vault
        case "insert":
            return f"INSERT INTO passwords(URL, UNAME, PASWD, NONCE) VALUES (\'{args[0]}\', \'{args[1]}\', \'{args[2]}\', \'{args[3]}\')"

        # [DELETE QUERIES]
        # DELETE a row from the vault
        # case "delete":
        #     return f"DELETE FROM passwords WHERE URL = \'{args[0]}\' AND UNAME = \'{args[1]}\' AND PASWD = \'{args[2]}\'"
        case "delete":
            return f"DELETE FROM passwords WHERE URL = \'{args[0]}\' AND UNAME = \'{args[1]}\'"


def sql_stash(query, args):
    match query:
        # [SELECT QUERIES]
        # Get the Last Accessed Date of a specified user
        case "get_lad":
            return f"SELECT LAD FROM users WHERE USER = \'{args}\'"

        # [UPDATE QUERIES]
        # UPDATE a row from the users database
        case "update_user":
            return f"UPDATE users SET MPWD = \'{args[0]}\' WHERE USER = \'{args[1]}\'"
        # Set the Last Accessed Date of a specified user
        case "set_lad":
            return f"UPDATE users SET LAD = \'{args[0]}\' WHERE USER = \'{args[1]}\'"


def sql_notes(query, args):
    match query:
        # [SELECT QUERIES]
        # SELECT a specific row from the vault
        case "select":
            return f"SELECT * FROM notes WHERE FILENAME = \'{args}\'"
        # SELECT every row from the vault
        case "print":
            return "SELECT FILENAME, CONTENT FROM notes"
        # SELET the nonce of a specific file
        case "select_nonce":
            return f"SELECT NONCE FROM notes WHERE FILENAME = \'{args}\'"

        # [UPDATE QUERIES]
        # UPDATE the filename of a row
        case "update_filename":
            return f"UPDATE notes SET FILENAME = \'{args[0]}\' WHERE FILENAME = \'{args[1]}\'"
        # UPDATE the content of a row
        case "update_content":
            return f"UPDATE notes SET CONTENT = \'{args[0]}\', NONCE = \'{args[1]}\' WHERE FILENAME = \'{args[2]}\'"

        # [INSERT QUERIES]
        # INSERT a new row into the vault
        case "insert":
            return f"INSERT INTO notes(FILENAME, CONTENT, NONCE) VALUES (\'{args[0]}\', \'{args[1]}\', \'{args[2]}\')"

        # [DELETE QUERIES]
        # DELETE a row from the vault
        case "delete":
            return f"DELETE FROM notes WHERE FILENAME = \'{args}\'"


def sql_otp(query, args):
    match query:
        # [SELECT QUERIES]
        # SELECT a specific row from the vault
        case "select":
            return f"SELECT * FROM otp WHERE ISSUER = \'{args}\'"
        # SELECT every row from the vault
        case "print":
            return "SELECT ISSUER, SECRET FROM otp"

        # [INSERT QUERIES]
        # INSERT a new row into the vault
        case "insert":
            return f"INSERT INTO otp(ISSUER, SECRET) VALUES (\'{args[0]}\', \'{args[1]}\')"

        # [DELETE QUERIES]
        # DELETE a row from the vault
        case "delete":
            return f"DELETE FROM otp WHERE ISSUER = \'{args[0]}\' AND SECRET = \'{args[1]}\'"
