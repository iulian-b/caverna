import hashlib
import os
import subprocess
import platform
import time

NETWORK_NAME = " "


########################################################################################################################
# Hashes a given username
# Arguments:
#  - str(user): the username
# Returns:
#  - str(hashed_user)
def sync_hash_user(user):
    return hashlib.sha256(bytes(user, 'utf-8')).hexdigest()


########################################################################################################################
def sync_db_is_synced(user) -> bool:
    userdb = "./caves/" + str(sync_hash_user(user)) + ".db"
    serverdb = "./server/" + str(sync_hash_user(user)) + ".db"
    user_time = os.path.getmtime(userdb)
    server_time = os.path.getmtime(serverdb)

    if user_time == server_time:
        return True


########################################################################################################################
def sync_get_creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return time.ctime(os.path.getctime(path_to_file))
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime


########################################################################################################################
def sync_db(user):
    return True


########################################################################################################################
def sync_check_network():
    wifi = subprocess.check_output(['netsh', 'WLAN', 'show', 'interfaces'])
    data = wifi.decode('utf-8')
    if NETWORK_NAME in data:
        print("connected to speccific wifi")
    else:
        print("not connected")
