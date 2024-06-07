import datetime
import hashlib
import os
import pickle
import socket
import subprocess
import platform
import urllib.request
import urllib.error
import requests
from ctypes import windll, wintypes, byref


import utils.db_tools as db_tools


########################################################################################################################
# Hashes a given username
# Arguments:
#  - str(user): the username
# Returns:
#  - str(hashed_user)
def sync_hash_user(user):
    return hashlib.sha256(bytes(user, 'utf-8')).hexdigest()


########################################################################################################################
# DEPRECATED
# def sync_get_creation_date(path_to_file):
#     """
#     Try to get the date that a file was created, falling back to when it was
#     last modified if that isn't possible.
#     See http://stackoverflow.com/a/39501288/1709587 for explanation.
#     """
#     if platform.system() == 'Windows':
#         return time.ctime(os.path.getctime(path_to_file))
#     else:
#         stat = os.stat(path_to_file)
#         try:
#             return stat.st_birthtime
#         except AttributeError:
#             # We're probably on Linux. No easy way to get creation dates here,
#             # so we'll settle for when its content was last modified.
#             return stat.st_mtime


########################################################################################################################
# Pings a given host
# Arguments:
#  - str(host): the address of the host
# Returns:
#  - subprocess.call(): the ping result
def sync_ping(host):
    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower() == 'windows' else '-c'

    # Building the command
    command = ['ping', param, '1', host]

    return subprocess.call(command) == 0


########################################################################################################################
# Establishes a handshake with the CAVERNA server
# Arguments:
#  - str(serverIP): the IP address of the server
# Returns:
#  - bool(True): handshake successfull
#  - bool(False): handshake unsuccessfull
def sync_handshake(serverIP):
    r = requests.get(f"http://{serverIP}/heartbeat")
    if r.status_code == 200:
        return True
    else:
        return False


########################################################################################################################
# Obfuscates the modification time and access time of a given file
# Arguments:
#  - str(filepath): the path of the file
def syncWIN32_obfuscate_mtime_atime(filepath):
    os.utime(filepath, (946677600, 946677600))


########################################################################################################################
# Obduscates the creation time of a given file
# Arguments:
#  - str(filepath): the path of the file
def syncWIN32_obfuscate_ctime(filepath):
    # Convert Unix timestamp to Windows FileTime using some magic numbers
    # See documentation: https://support.microsoft.com/en-us/help/167296
    timestamp = int(125911512000000000)
    ctime = wintypes.FILETIME(timestamp & 0xFFFFFFFF, timestamp >> 32)

    # Call Win32 API to modify the file creation date
    handle = windll.kernel32.CreateFileW(filepath, 256, 0, None, 3, 128, None)
    windll.kernel32.SetFileTime(handle, byref(ctime), None, None)
    windll.kernel32.CloseHandle(handle)


########################################################################################################################
# Ofduscates ctime, mtime and atime of all files in a given directory, depending on the running platform
# Arguments:
#  - str(dir): the path of the directory
def sync_obfuscate_all_fragments(dir):
    # Get all files in directory
    files = os.listdir(dir)

    # If the platform is Windows
    if platform.system() == "Windows":
        for f in files:
            # Get a filepath
            fpath = f"{dir}/{f.title()}"

            # Obfuscate creation time
            syncWIN32_obfuscate_ctime(fpath)

            # Obfuscate modification and access times
            syncWIN32_obfuscate_mtime_atime(fpath)

    # If the platform is Linux
    elif platform.system() == "Linux":
        for f in files:
            # Get a filepath
            fpath = f"{dir}/{f.title()}"

            # Obfuscate modification and access times
            os.utime(fpath, (946677600, 946677600))

            # Linux does not have creation time
            # :)


########################################################################################################################
# Sets the Last Accessed DateTime of a given user to the current timestamp
# Arguments:
#  - str(user): the username
def sync_set_user_lad(user):
    # Connect to _users stash
    conn = db_tools.db_stash_connect()
    c = conn.cursor()

    # Get timestamp
    timestamp = datetime.datetime.now()

    # Hash username
    user = sync_hash_user(user)

    # Set LAD
    c.execute(db_tools.sql_stash("set_lad", (str(timestamp), user)))
    conn.commit()

    # Close connection
    conn.close()


########################################################################################################################
# Retrieves the Last Accessed DateTime of a given user
# Arguments:
#  - str(user): the username
# Returns:
#  - str(LAD): the user's LAD
def sync_get_user_lad(user):
    # Connect to _users stash
    conn = db_tools.db_stash_connect()
    c = conn.cursor()

    # Hash username
    user = sync_hash_user(user)

    # Get LAD
    c.execute(db_tools.sql_stash("get_lad", user))
    conn.commit()
    res = c.fetchone()

    # Return user LAD
    return res[0]


########################################################################################################################
# Checks wherever a given user's database fragments are ahead or behind the server
# Arguments:
#  - str(user): the username
#  - str(SERVER_IP): the IP address of the server
# Returns:
#  - bool(True): if the user is ahead of the server
#  - bool(False): if the server is ahead of the user
def sync_check_update(user, SERVER_IP):
    # Get user time
    USER_TIME = sync_get_user_lad(user)

    # Make request
    r = requests.post(f'http://{SERVER_IP}/stime', json={
        "usr": sync_hash_user(user),
        "time": str(USER_TIME)
    })

    # Get server time
    SERVER_TIME = r.json()["stime"]
    SERVER_TIME = datetime.datetime.strptime(SERVER_TIME, '%Y-%m-%d %H:%M:%S.%f')
    USER_TIME = datetime.datetime.strptime(USER_TIME, '%Y-%m-%d %H:%M:%S.%f')

    if USER_TIME > SERVER_TIME:
        return True
    else:
        return False


########################################################################################################################
# Adds a given user to the server
# Arguments:
#  - str(user): the username
#  - str(mpwd_hash): the hash of the user's master password
#  - str(SERVER_IP): the IP address of the server
# Returns:
#  - int(requests.status_code): the status code of the post request
def sync_server_add_user(user, mpwd_hash, SERVER_IP):
    # Get user hash
    user_hash = sync_hash_user(user)

    # Make request
    r = requests.post(f'http://{SERVER_IP}/adduser', json={
        "usr": user_hash,
        "mpwd": mpwd_hash
    })

    return r.status_code


########################################################################################################################
# Uploads the a given user's local fragments to the server
# Arguments:
#  - str(user): the username
#  - str(secret): the user's secret
#  - str(SERVER_IP): the IP address of the server
def sync_upload(user, secret, SERVER_IP):
    counter = 0
    while (1):
        # Generate hash with the user + pepper + n
        split_filename = sync_hash_user(user + secret + str(counter))

        # Get fragment
        if os.path.exists(f"caves/{split_filename}.cvrn"):

            # Upload file
            with open(f"caves/{split_filename}.cvrn", 'rb') as file:
                requests.post(f"http://{SERVER_IP}/upload", files={'file': file})

            # Advance counter
            counter += 1
        else:
            break


########################################################################################################################
# Downloads the a given user's fragments from the server
# Arguments:
#  - str(user): the username
#  - str(secret): the user's secret
#  - str(SERVER_IP): the IP address of the server
def sync_download(user, secret, SERVER_IP):
    counter = 0
    while (1):
        split_filename = sync_hash_user(user + secret + str(counter))
        try:
            urllib.request.urlretrieve(f"http://{SERVER_IP}/download/" + split_filename + ".cvrn",
                                       f"caves/{split_filename}.cvrn")
            counter += 1

        except FileNotFoundError:
            print(FileNotFoundError)
            break
        except urllib.error.HTTPError:
            print(urllib.error.HTTPError)
            break
        except urllib.error.URLError:
            print(urllib.error.URLError)
            break
        except Exception as e:
            print(e)
            break


########################################################################################################################
# Checks if a given user is present in the server's stash
# Arguments:
#  - str(user_hash): the hash of the user's username
#  - str(SERVER_IP): the IP address of the server
# Returns:
#  - int(requests.status_code): the status code of the post request
def sync_check_user(user_hash, SERVER_IP):
    r = requests.post(f'http://{SERVER_IP}/checkusr', json={
        'usr': user_hash,
    })
    return r.status_code


########################################################################################################################
# Obduscates the fragments on the server
# Arguments:
#  - str(SERVER_IP): the IP address of the server
# Returns:
#  - int(requests.status_code): the status code of the post request
def sync_obfuscate_server(SERVER_IP):
    r = requests.get(f"http://{SERVER_IP}/obf")
    return r.status_code


########################################################################################################################
# Saves the given network and server names to a pickle file
# Arguments:
#  - str(network): the network SSID
#  - str(server): the IP address of the server
def sync_save_settings(network, server):
    data = [network, server]
    with open('data.pickle', 'wb') as file:
        pickle.dump(data, file)


########################################################################################################################
# Loads the saved settings from a pickle file
# Returns:
#   - file(pickle): the file containing the saved settings
def sync_load_settings():
    with open('data.pickle', 'rb') as file:
        return pickle.load(file)


########################################################################################################################
# Checks if the current device is connected to a given network
# Arguments:
#   - str(network): the network
# Returns:
#   - bool(True): if it's connected to the network
#   - bool(False): if it's not connected to the network
def sync_check_network(network, serverIP):
    try:
        interfaces = subprocess.check_output(['netsh', 'WLAN', 'show', 'interfaces'])
        data = interfaces.decode('utf-8')
        if network in data:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(serverIP)
            if result == 0:
                sock.close()
                return True
            else:
                sock.close()
                return False
        else:
            return False
    except Exception as e:
        return False
