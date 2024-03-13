from pysqlcipher3 import dbapi2 as sqlcipher


# USERS
def db_user_connect(user, mpwd_hash):
    conn = sqlcipher.connect("caves/" + user + ".db")
    c = conn.cursor()
    c.execute(f"PRAGMA key='{mpwd_hash}'")
    c.execute("PRAGMA cipher_compatibility = 3")
    conn.commit()
    c.close()
    return conn


def db_stash_connect():
    conn = sqlcipher.connect("caves/_users.db")
    c = conn.cursor()
    c.execute("PRAGMA key='b6QF9hAgPM6tCbrSMpO+MI335ShsQEodb6fudPE'")
    c.execute("PRAGMA cipher_compatibility = 3")
    return conn


def db_user_initialize(user, mpwd):
    conn = db_user_connect(user, mpwd)
    c = conn.cursor()
    c.execute("""CREATE TABLE caverna (
	    ID INTEGER PRIMARY KEY,
   	    URL TEXT NOT NULL,
	    UNAME TEXT,
	    PASWD TEXT NOT NULL,
	    PASWD_NONCE TEXT
    )""")
    conn.commit()
    c.close()


# GENERAL
def db_add_user(user, mpwd_hash):
    key = mpwd_hash[-32:]
    conn = db_stash_connect()
    c = conn.cursor()
    c.execute(f"INSERT INTO users(NAME, HASH) VALUES(\'{user}\', \'{mpwd_hash}\')")
    conn.commit()
    c.close()


def db_user_get_hash(user):
    conn = db_stash_connect()
    c = conn.cursor()
    c.execute(f"SELECT HASH FROM users WHERE NAME = '{user}'")
    salt = c.fetchone()
    return salt[0]


def sql(query, args):
    match query:
        case "insert":
            return f"INSERT INTO caverna(URL, UNAME, PASWD, PASWD_NONCE) VALUES (\'{args[0]}\', \'{args[1]}\', \'{args[2]}\', \'{args[3]}\')"
        case "delete":
            return f"DELETE FROM caverna WHERE URL = \'{args[0]}\' AND UNAME = \'{args[1]}\' AND PASWD = \'{args[2]}\'"
        case "update_row":
            return f"UPDATE caverna SET URL = \'{args[0]}\', UNAME = \'{args[1]}\', PASWD = \'{args[2]}\', PASWD_NONCE = \'{args[3]}\' WHERE URL = \'{args[4]}\' AND UNAME = \'{args[5]}\' AND PASWD = \'{args[6]}\'"
        case "select":
            return f"SELECT * FROM caverna WHERE URL = \'{args[0]}\' AND UNAME = \'{args[1]}\' AND PASWD = \'{args[2]}'"
        case "print":
            return "SELECT URL, UNAME, PASWD FROM caverna"
        case "update_user":
            return f"UPDATE users SET HASH = \'{args[1]}\' WHERE NAME = \'{args[0]}\'"
        case "select_nonce":
            return f"SELECT PASWD_NONCE FROM caverna WHERE UNAME = \'{args[0]}\' AND PASWD = \'{args[1]}\'"
        case "select_paswd":
            return f"SELECT PASWD FROM caverna WHERE URL = \'{args[0]}\' AND UNAME = \'{args[1]}\'"
