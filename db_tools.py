from pysqlcipher3 import dbapi2 as sqlcipher


# USERS
def db_user_connect(user, mpwd):
    conn = sqlcipher.connect("caves/" + user + ".db")
    c = conn.cursor()
    c.execute(f"PRAGMA key='{mpwd}'")
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
	    PASWD TEXT NOT NULL UNIQUE
    )""")
    conn.commit()
    c.close()


# GENERAL
def db_add_user(user, salt):
    conn = db_stash_connect()
    c = conn.cursor()
    c.execute("INSERT INTO users('USER', 'SALT') VALUES(\"" + user + "\",\"" + salt + "\");")
    conn.commit()
    c.close()


def db_user_get_salt(user):
    conn = db_stash_connect()
    c = conn.cursor()
    c.execute(f"SELECT SALT FROM users WHERE USER = '{user}'")
    salt = c.fetchone()
    return salt[0]


def sql(query):
    match query:
        case "insert":
            return """INSERT INTO vault("URL", "UNAME", "PASWD") VALUES (%s, %s, %s)"""
        case "delete":
            return """DELETE FROM vault WHERE URL = %s"""
        case "update":
            return """UPDATE vault SET URL = %s WHERE URL = %s"""
        case "update_uname":
            return """UPDATE vault SET UNAME = %s WHERE URL = %s"""
        case "update_paswd":
            return """UPDATE vault SET PASWD = %s WHERE URL = %s"""
        case "select":
            return """SELECT * FROM vault WHERE URL = %s"""
        case "update":
            return """UPDATE vault SET PASWD = %s"""
        case "print_pwds":
            return """SELECT * FROM caverna"""
