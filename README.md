# Backup My Accounts

A backup-tool for multiple cloud-services

Currently supported:
- Github
- Google Drive
- Google Photos
- WordPress
- Dropbox

Google and Dropbox will need some minor preparations, see below for details

## Prerequisites
```sh
sudo apt install python3 python3-urllib3 sshpass
```

```sh
pip3 install -r requirements.txt
```

## Add accounts
To add an account to backup run
```sh
$ python3 backup.py --add
```

and follow the instructions

## Backup accounts
To start the backup run
```sh
$ python3 backup.py --backup [alias1, alias2]
```

If you provide aliases, only those accounts will be backed up.

## Setup E-Mail notifications
Note that this feature will currently only work with Gmail
On first start the script will ask for Gmail credentials for notifications.  
If you choose to enable this feature, enter your Gmail-Account as "Mail user" and an "app password" as "Mail password".  
Check out (this link)[https://support.google.com/accounts/answer/185833] for how to obtain an app password.

## Setup Google-Backup
1. Go to https://console.developers.google.com/
2. Create a project
3. On the left select "Dashboard"
4. Select "Activate APIs and services"
5. Activate both Google Drive API and Photos Library API
6. On the left select "Credentials"
7. Create an OAuth-Client-ID for "Others"
8. Download the generated credentials json
9. When prompted by the script, paste the content of that json

## Setup Dropbox-Backup
1. Go to https://www.dropbox.com/developers/apps
2. Click "Create app"
3. Select "Dropbox API"
4. Select "Full Dropbox"
5. Give it a name
6. Click "Create app"
7. Under "Generated access token" click "Generate"
8. When prompted by the script, paste that token

## How it works
1. Github
    - Goes through all your repositories and backs up the latest release
    - Saves each repository as [repository_name]-[tag].zip (e.g. my-project-1.0.zip)
    - Older versions of the same repository will be removed (so there's only the most recent version backed up)
2. Google Drive
    - Mirrors the folder structure of your Drive to your backup-path
    - For regular files it compares the MD5-Hash to determine whether to download it or not (to avoid overhead)
    - Google Docs and Spreadsheets (for which no MD5 is provided by the API), will be backed up every time and exported as .pdf and .xlsx respectively
3. Google Photos
    - Uses album-names to create a folder structure
    - An album "2018-12-24 Christmas" will be backed up to /your/backup/folder/2018/2018-01-01 Christmas/
    - All other albums go to /your/backup/folder/0000/[albumname]
    - Since there's no MD5-Hashes for images either, the script simply uses the original filename to determine if it should download the image or not
4. WordPress
    - Backs up your database into a folder "backups/" in the server's home directory
    - Backs up all files in the server's home directory (excluding the backups) into that folder
    - Removes all but the last 5 backups
    - Syncs the backup folder to the backup folder you specified
5. Dropbox
    - Mirrors the folder structure of your Dropbox to your backup-path
	- Checks for content hash to determine whether to download it or not (to avoid overhead)
