import hashlib
import os
import subprocess
import platform
import time
from ctypes import windll, wintypes, byref

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


########################################################################################################################
def sync_obfuscate_mtime_atime(filepath):
    os.utime(filepath, (946677600, 946677600))


########################################################################################################################
def sync_obfuscate_ctime(filepath):
    # Convert Unix timestamp to Windows FileTime using some magic numbers
    # See documentation: https://support.microsoft.com/en-us/help/167296
    timestamp = int(125911512000000000)
    ctime = wintypes.FILETIME(timestamp & 0xFFFFFFFF, timestamp >> 32)

    # Call Win32 API to modify the file creation date
    handle = windll.kernel32.CreateFileW(filepath, 256, 0, None, 3, 128, None)
    windll.kernel32.SetFileTime(handle, byref(ctime), None, None)
    windll.kernel32.CloseHandle(handle)


########################################################################################################################
def sync_obfuscate_all_fragments(dir):
    files = os.listdir(dir)
    for f in files:
        fpath = f"{dir}/{f.title()}"
        sync_obfuscate_ctime(fpath)
        sync_obfuscate_mtime_atime(fpath)