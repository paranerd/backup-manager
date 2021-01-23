import os
import time
import datetime
import shutil
import hashlib
from pathlib import Path

def remove(path):
    if os.path.isfile(path):
        os.remove(path)
    else:
        shutil.rmtree(path)

def create_folder(path):
    """
    Create folder if not exists

    @param string path Absolute path to folder
    @return string
    """
    if not os.path.exists(path):
        os.makedirs(path)
        return path

def remove_folder(path):
    """
    Remove folder recursively

    @param string path
    """
    shutil.rmtree(path)

def md5(string):
    """
    Calculate MD5-Checksum of string

    @param string string
    @return string
    """
    m = hashlib.md5()
    m.update(string.encode('utf-8'))
    return m.hexdigest()

def md5_file(path):
    """
    Generate MD5-Hash of a file

    @param string path Path to file
    @return string
    """
    if not os.path.isfile(path):
        return ""

    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_timestamp(format=False):
    """
    Get current timestamp

    @param boolean format
    @return string|int
    """
    if format:
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        return int(round(time.time() * 1000))

def get_project_path():
    """
    Return absolute path of project folder

    @return string
    """
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def create_backup_path(path, alias):
    backup_path = path if path else 'backups/' + alias

    if not backup_path.startswith("/"):
        backup_path = get_project_path() + "/" + backup_path

    if not os.path.exists(backup_path):
        os.makedirs(backup_path)

    return backup_path

def cleanup_versions(dir, versions, prefix=""):
    """
    Remove all but the latest x files in a folder
    """
    # Get directory content
    folders = os.listdir(dir)

    # Get absolute paths for all items
    folders = [os.path.join(dir, f) for f in folders]

    # Filter for prefix
    folders = list(filter(lambda x: os.path.basename(x).startswith(prefix), folders))

    # Filter by modification date descending
    folders.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    for folder in folders[versions:]:
        remove(folder)

def get_tmp_path():
    """
    Gets absolute path of temporary folder
    """
    tmp_path = os.path.join(Path(__file__).parent.parent.absolute(), 'tmp')
    Path(tmp_path).mkdir(parents=True, exist_ok=True)

    return tmp_path