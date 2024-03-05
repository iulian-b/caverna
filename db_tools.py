import psycopg2


def db_connect():
    conn = psycopg2.connect(
        dbname="caverna",
        user="ibocse",
        password="spirudb123!",
        host="127.0.0.1",
        port="49153"
    )
    #return psycopg2.connect("dbname=caverna user=ibocse password=spirudb123!")
    return conn


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
        case "print":
            return """SELECT * FROM vault"""
