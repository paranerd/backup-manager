import os
import time
import datetime
import hashlib

def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        return path

def md5(string):
    m = hashlib.md5()
    m.update(string.encode('utf-8'))
    return m.hexdigest()

##
# Generate MD5-Hash of a file
#
# @param path Path to file
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

def log(msg):
    print(get_timestamp(True) + " | " + str(msg))

def get_timestamp(format=False):
    if format:
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        return int(round(time.time() * 1000))
