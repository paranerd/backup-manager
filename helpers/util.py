"""Convenience helpers."""

import os
import datetime
import shutil
import hashlib
from pathlib import Path

startup_time = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')

def remove(path):
    """
    Remove file or directory (recursively).

    @param string path
    """
    if os.path.isfile(path):
        os.remove(path)
    else:
        shutil.rmtree(path)

def create_folder(path):
    """
    Create folder if not exists.

    @param string path Absolute path to folder
    @return string
    """
    if not os.path.exists(path):
        os.makedirs(path)

        return path

def remove_folder(path):
    """
    Remove folder recursively.

    @param string path
    """
    shutil.rmtree(path)

def md5(string):
    """
    Calculate MD5-Checksum of string.

    @param string string
    @return string
    """
    checksum = hashlib.md5()
    checksum.update(string.encode('utf-8'))

    return checksum.hexdigest()

def md5_file(path):
    """
    Generate MD5-Hash of a file.

    @param string path Path to file
    @return string
    """
    if not os.path.isfile(path):
        return ''

    checksum = hashlib.md5()
    with open(path, 'rb') as fin:
        for chunk in iter(lambda: fin.read(4096), b''):
            checksum.update(chunk)

    return checksum.hexdigest()

def get_project_path():
    """
    Get absolute path of project folder.

    @return string
    """
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def cleanup_versions(backup_path, versions, prefix=''):
    """
    Remove all but the latest x files in a folder.
    """
    # Get directory content
    items = os.listdir(backup_path)

    # Get absolute paths for all items
    items = [os.path.join(backup_path, item) for item in items]

    # Filter for prefix
    items = list(filter(lambda item: os.path.basename(item).startswith(prefix + '_'), items))

    # Filter by modification date descending
    items.sort(key=os.path.getmtime, reverse=True)

    for item in items[versions:]:
        remove(item)

def get_tmp_path():
    """
    Get absolute path of temporary folder.
    """
    tmp_path = os.path.join(Path(__file__).parent.parent.absolute(), 'tmp')
    Path(tmp_path).mkdir(parents=True, exist_ok=True)

    return tmp_path

def create_tmp_folder():
    """
    Create a folder in the tmp folder.

    @return string
    """
    tmp_path = os.path.join(get_tmp_path(), md5(str(datetime.datetime.now().timestamp())))
    Path(tmp_path).mkdir(parents=True, exist_ok=True)

    return tmp_path
