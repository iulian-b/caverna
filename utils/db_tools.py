# Sqlcipher package
from pysqlcipher3 import dbapi2 as sqlcipher


########################################################################################################################
# Connects a given user to its own vault database by using his master password hash as the key to decrypt the database
# Arguments:
#  - str(user) the username
#  - str(mpwd_hash) the user's master password hash
# Returns:
#  - sqlcipher(connection)
def db_user_connect(user, mpwd_hash):
    # Connect to the user's database
    conn = sqlcipher.connect("caves/" + user + ".db")
    c = conn.cursor()

    # Set the key to the mpwd hash
    c.execute(f"PRAGMA key='{mpwd_hash}'")

    # This is not necessary for it to work, but i don't trust noboy these days
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
    conn = db_user_connect(user, mpwd)
    c = conn.cursor()

    # Exectute the CREATE TABLE query
    c.execute("""CREATE TABLE caverna (
	    ID INTEGER PRIMARY KEY,
   	    URL TEXT NOT NULL,
	    UNAME TEXT,
	    PASWD TEXT NOT NULL,
	    PASWD_NONCE TEXT
    )""")

    # Terminate the connection
    conn.commit()
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

    # Execute the INSERT query which adds the username and mpwd hash to the 'users' table
    c.execute(f"INSERT INTO users(NAME, HASH) VALUES(\'{user}\', \'{mpwd_hash}\')")

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

    # Execute the SELECT query which returns the user's mpwd hash
    c.execute(f"SELECT HASH FROM users WHERE NAME = '{user}'")
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
def sql(query, args):
    match query:
        # [SELECT QUERIES]
        # SELECT a specific row from the vault
        case "select":
            return f"SELECT * FROM caverna WHERE URL = \'{args[0]}\' AND UNAME = \'{args[1]}\' AND PASWD = \'{args[2]}'"
        # SELECT every row from the vault
        case "print":
            return "SELECT URL, UNAME, PASWD FROM caverna"
        # SELECT only the nonce from the vault
        case "select_nonce":
            return f"SELECT PASWD_NONCE FROM caverna WHERE UNAME = \'{args[0]}\' AND PASWD = \'{args[1]}\'"
        # SELECT only the encrypted password from the vault
        case "select_paswd":
            return f"SELECT PASWD FROM caverna WHERE URL = \'{args[0]}\' AND UNAME = \'{args[1]}\'"
        # SELECT all encrypted passwords and nonces from the vault
        case "select_all_paswd_crypto":
            return f"SELECT PASWD, PASWD_NONCE FROM caverna"

        # [UPDATE QUERIES]
        # UPDATE a row from the vault
        case "update_row":
            return f"UPDATE caverna SET URL = \'{args[0]}\', UNAME = \'{args[1]}\', PASWD = \'{args[2]}\', PASWD_NONCE = \'{args[3]}\' WHERE URL = \'{args[4]}\' AND UNAME = \'{args[5]}\' AND PASWD = \'{args[6]}\'"
        # UPDATE the encrypted password and nonce from the vault
        case "update_crypto":
            return f"UPDATE caverna SET PASWD = \'{args[0]}\', PASWD_NONCE = \'{args[1]}\' WHERE PASWD = \'{args[2]}\' AND PASWD_NONCE = \'{args[3]}\'"
        # UPDATE a row from the users database
        case "update_user":
            return f"UPDATE users SET HASH = \'{args[1]}\' WHERE NAME = \'{args[0]}\'"

        # [INSERT QUERIES]
        # INSERT a new row into the vault
        case "insert":
            return f"INSERT INTO caverna(URL, UNAME, PASWD, PASWD_NONCE) VALUES (\'{args[0]}\', \'{args[1]}\', \'{args[2]}\', \'{args[3]}\')"

        # [DELETE QUERIES]
        # DELETE a row from the vault
        case "delete":
            return f"DELETE FROM caverna WHERE URL = \'{args[0]}\' AND UNAME = \'{args[1]}\' AND PASWD = \'{args[2]}\'"
