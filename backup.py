import os
import sys

from modules.github import Github_Backup
from modules.googledrive import Google_Drive_Backup
from modules.googlephotos import Google_Photos_Backup

config_location = os.path.join(os.path.dirname(__file__), "config.json")
cache_location = os.path.join(os.path.dirname(__file__), "cache")

if not os.path.exists(config_location):
    with open(config_location, 'w') as config:
        config.write('{}')

if not os.path.exists(cache_location):
    os.makedirs(cache_location)

git = Github_Backup()
gd = Google_Drive_Backup()
gp = Google_Photos_Backup()

git.backup()
gd.backup()
gp.backup()
