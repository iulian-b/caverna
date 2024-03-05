import getpass
import hashlib
import sys
import argparse

import pwd_tools
import db_tools


def main():
    parsarg = argparse.ArgumentParser(description="Description")
    #mpwd_input = getpass.getpass("Master Password: ").encode()
    mpwd_input = "spiruharet123!".encode()
    twofa = "dee boo dah".encode()
    mpwd_hash = hashlib.sha256(mpwd_input + twofa).hexdigest()

    # if pwd_tools.mpwd_query(mpwd_input, twofa) is True:
    conn = db_tools.db_connect()
        # print("Connected to db")
    # else:
    #     print("Failed to connect to db")
    #     sys.exit()

    parsarg.add_argument("-a", "--add", type=str, nargs=2, help="Add entry", metavar=("[URL]", "[USERNAME]"))
    parsarg.add_argument("-q", "--query", type=str, nargs=1, help="Query entry", metavar="[URL]")
    parsarg.add_argument("-l", "--list", action="store_true", help="List entries")
    parsarg.add_argument("-d", "--delete", type=str, nargs=1, help="Delete entry", metavar="[URL]")
    parsarg.add_argument("-ap", "--add_pwd", type=str, nargs=3, help="Add manual entry",
                         metavar=("[URL]", "[USERNAME]", "[PASSWORD]"))
    parsarg.add_argument("-uurl", "--upd_url", type=str, nargs=2, help="Update URL", metavar=("[NEW_URL]", "[OLD_URL]"))
    parsarg.add_argument("-uuname", "--upd_username", type=str, nargs=2, help="Update Username",
                         metavar=("[URL]", "[URL_USERNAME]"))
    parsarg.add_argument("-uupwd", "--upd_password", type=str, nargs=2, help="Update Password",
                         metavar=("[URL]", "[URL_PASSWORD]"))
    parsarg.add_argument("-su", "--setup", action="store_true", help="first setup")

    args = parsarg.parse_args()
    cursor = conn.cursor()
    conn.commit()

    if args.add:
        pwd = pwd_tools.encrypt(pwd_tools.pwd_gen(20), mpwd_hash)
        cursor.execute(db_tools.sql("insert"), (args.add[0], args.add[1], pwd))
        print("Record added")

    if args.query:
        # cursor.execute(db_tools.sql("select"), args.query[0])
        cursor.execute(f"SELECT * FROM vault WHERE \"URL\" = \'{args.query[0]}\'")
        record = cursor.fetchone()
        pwd_decrypted = pwd_tools.decrypt(record[2], mpwd_hash
                                          )
        if bool(record):
            print("Record: " + "\n URL: {0}, UNAME: {1}, PWD: {2}".format(record[0], record[1], record[2],
                                                                          pwd_decrypted.decode('utf-8')))
            print("Record with encrypted pwd: " + "\n URL: {0}, UNAME: {1}, PWD: {2}".format(record[0], record[1],
                                                                                             record[2]))
        else:
            print("Error argparse.query")

    if args.list:
        cursor.execute(db_tools.sql("print"))
        record = cursor.fetchall()

        for i in range(len(record)):
            entry = record[i]
            for j in range(len(entry)):
                titles = ["ID", "URL: ", "UNAME: ", "PASWD: "]
                if titles[j] == "PASWD: ":
                    bytes_row = entry[j]
                    pwd = pwd_tools.decrypt(bytes_row, mpwd_hash)
                    print("PASWD: " + str(pwd.decode('utf-8')))
                else:
                    print(str(titles[j]) + str(entry[j]))
            print("----------")

    if args.delete:
        cursor.execute(db_tools.sql("delete"), args.delete[0])
        print("Record deleted")

    if args.add_pwd:
        pwd_encrypted = pwd_tools.encrypt(args.add_pwd[2], mpwd_hash)
        cursor.execute(db_tools.sql("insert"), (args.add_pwd[0], args.add_pwd[1], pwd_encrypted))
        print("Record added with custom pwd")

    if args.upd_url:
        cursor.execute(db_tools.sql("update"), (args.upd_url[0], args.upd_url[1]))
        print("Updated url")

    if args.upd_username:
        cursor.execute(db_tools.sql("update_uname"), (args.upd_username[0], args.upd_username[1]))
        print("Updated username")

    if args.upd_password:
        print("Old pwd:")
        cursor.execute(db_tools.sql("update_paswd"), (args.upd_password[0], args.upd_password[1]))
        print("Updated password")

    if args.setup:
        print("setup")

    conn.commit()
    cursor.close()


if __name__ == "__main__":
    main()
