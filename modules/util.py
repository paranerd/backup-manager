import os
import time
import datetime
import hashlib

project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
log_name = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S') + ".log"
backup_path = os.path.join(project_path, "log", log_name)

##
# Create folder if not exists
#
# @param string path Absolute path to folder
#
# @return string
def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        return path

##
# Calculate MD5-Checksum of string
#
# @param string string
#
# @return string
def md5(string):
    m = hashlib.md5()
    m.update(string.encode('utf-8'))
    return m.hexdigest()

##
# Generate MD5-Hash of a file
#
# @param string path Path to file
#
# @return string
def md5_file(path):
    if not os.path.isfile(path):
        return ""

    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

##
# Get current timestamp
#
# @param boolean format
#
# @return string|int
def get_timestamp(format=False):
    if format:
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        return int(round(time.time() * 1000))

##
# Write message to log and print to console
#
# @param string msg
def log(msg):
    # Create backup folder
    create_folder(os.path.dirname(backup_path))

    # Build message
    msg = get_timestamp(True) + " | " + str(msg)

    # Print message to terminal
    print(msg)

    # Write message to file
    with open(backup_path, "a") as log:
        log.write(msg + "\n")
