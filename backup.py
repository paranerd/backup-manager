import os

from modules.github import Github_Backup
from modules.googledrive import Google_Drive_Backup
from modules.googlephotos import Google_Photos_Backup

if not os.path.exists('config.json'):
    with open('config.json', 'w') as config:
        config.write('{}')

git = Github_Backup()
gd = Google_Drive_Backup()
gp = Google_Photos_Backup()

git.backup()
gd.backup()
gp.backup()
