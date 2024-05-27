import datetime
import os
import platform

from pysqlcipher3 import dbapi2 as sqlcipher
from flask import Flask, request, jsonify, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from ctypes import windll, wintypes, byref

app = Flask(__name__)
HOST = "192.168.1.112"
PORT = 1999
AUTH = False

UPLOAD_FOLDER = 'caves'
ALLOWED_EXTENSIONS = {'cvrn'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.urandom(12).hex()

########################################################################################################################
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

########################################################################################################################
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

def get_server_user_time(user):
    # Connect to stash
    server_conn = db_stash_connect()
    server_cursor = server_conn.cursor()

    # Get stored LAD
    server_cursor.execute(f"SELECT LAD FROM users WHERE USER = \'{user}\'")
    res = server_cursor.fetchone()
    time_check = datetime.datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S.%f')

    server_conn.close()
    return str(time_check)
########################################################################################################################

def db_add_user(user_hash, mpwd_hash):
    # Connect to the _users database
    conn = db_stash_connect()
    c = conn.cursor()

    # Get the current timestamp as the LAD
    timestamp = datetime.datetime.now()

    # Execute the INSERT query which adds the username and mpwd hash to the 'users' table
    c.execute(f"INSERT INTO users(USER, MPWD, LAD) VALUES(\'{user_hash}\', \'{mpwd_hash}\', \'{timestamp}\')")

    # Terminate the connection
    conn.commit()
    c.close()

########################################################################################################################
def syncWIN32_obfuscate_mtime_atime(filepath):
    os.utime(filepath, (946677600, 946677600))


########################################################################################################################
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

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    if request.method == 'GET':
        return '', 200

@app.route('/checkusr', methods=['POST'])
def check_usr():
    if request.method == 'POST':
        content = request.json
        USERNAME = content['usr']

        conn = db_stash_connect()
        c = conn.cursor()

        c.execute(f"SELECT USER FROM users WHERE USER = \'{USERNAME}\'")
        conn.commit()

        res = c.fetchall()
        conn.close()

        if USERNAME in str(res):
            return '', 200
        else:
            return '', 400

@app.route('/adduser', methods=['POST'])
def add_usr():
    if request.method == 'POST':
        content = request.json
        USER = content['usr']
        MPWD = content['mpwd']
        db_add_user(USER, MPWD)
        return '', 200

@app.route('/stime', methods=['POST'])
def stime():
    if request.method == 'POST':
        content = request.json
        USER = content['usr']
        # USER_TIME = content['time']

        SERVER_TIME = get_server_user_time(USER)

        return jsonify({"stime": SERVER_TIME})


@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        files = request.files.getlist("file")
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        for file in files:
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return '', 200

@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    return send_from_directory('../test/caves', filename)

@app.route('/obf', methods=['GET'])
def obfuscate():
    dir = "../test/caves/"
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

            return '', 200

    # If the platform is Linux
    elif platform.system() == "Linux":
        for f in files:
            # Get a filepath
            fpath = f"{dir}/{f.title()}"

            # Obfuscate modification and access times
            os.utime(fpath, (946677600, 946677600))

            return '', 200

            # Linux does not have creation time
            # :)

    return '', 404

########################################################################################################################
if __name__ == "__main__":
    app.run(host=HOST, debug=True, port=PORT)
