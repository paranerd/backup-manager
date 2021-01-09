# Backup My Accounts

A backup-tool for multiple cloud-services

Currently supported:
- GitHub
- Google Drive
- Google Photos
- Linux Server
- MySQL Database
- WordPress
- Dropbox

Google and Dropbox will need some minor preparations, see below for details

## Prerequisites
```sh
sudo apt install python3 python3-urllib3 sshpass mysql-clients
```

```sh
pip3 install -r requirements.txt
```

If you want to back up GitHub non-archived, `git` must also be installed and configured

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

## Set up E-Mail notifications
Note that this feature will currently only work with Gmail

On first start the script will ask for Gmail credentials for notifications.

If you choose to enable this feature, enter your Gmail-Account as "Mail user" and an "App Password" as "Mail password".

Check out [this link](https://support.google.com/accounts/answer/185833) for how to obtain an app password.

## Set up Google-Backup
1. [Open google cloud console](https://console.developers.google.com/)
2. Choose or create a project
3. [Activate Drive API](https://console.developers.google.com/apis/library/drive.googleapis.com)
4. [Activate Photos API](https://console.developers.google.com/apis/library/photoslibrary.googleapis.com)
5. [Create consent page](https://console.developers.google.com/apis/credentials/consent)
6. Choose "External"
7. Enter a name and click "Save"
8. [Open credentials page](https://console.developers.google.com/apis/credentials)
9. Click on "Create Credentials" -> OAuth-Client-ID -> Desktop Application
10. Ignore the pop-up
11. Download the client ID JSON
12. When prompted by the script, paste the content of that json

## Set up Dropbox-Backup
1. [Open Dropbox developers page](https://www.dropbox.com/developers/apps)
2. Click "Create app"
3. Select "Dropbox API"
4. Select "Full Dropbox"
5. Give it a name
6. Click "Create app"
7. Under "Generated access token" click "Generate"
8. When prompted by the script, paste that token

## Set up GitHub-Backup
Follow [this documentation](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token#creating-a-token) to create your personal access token.

You will be prompted for it when adding a GitHub backup

## How it works
1. GitHub
    - Archive
        - Goes through all your repositories and backs up the latest release
        - Saves each repository as [repository_name]-[tag].zip (e.g. my-project-1.0.zip)
        - Older versions of the same repository will be removed (so there's only the most recent version backed up)
    - Non-archive
        - Uses `git` (requires `git` to be set up) to `clone` or `pull --rebase`
2. GitHub Gist
    - Archive
        - Goes through all your gists and backs up the latest release
        - Saves each repository as [gist-id]-[name of first file]-[hashed-update-datetime].zip (e.g. my-project-1.0.zip)
        - Older versions of the same gist will be removed (so there's only the most recent version backed up)
    - Non-archive
        - Uses `git` (requires `git` to be set up) to `clone` or `pull --rebase`
2. Google Drive
    - Mirrors the folder structure of your Drive to your backup-path
    - For regular files it compares the MD5-Hash to determine whether to download it or not (to avoid overhead)
    - Google Docs and Spreadsheets (for which no MD5 is provided by the API), will be backed up every time and exported as .pdf and .xlsx respectively
3. Google Photos
    - Uses album-names to create a folder structure
    - An album "2018-12-24 Christmas" will be backed up to /your/backup/folder/2018/2018-01-01 Christmas/
    - All other albums go to /your/backup/folder/0000/[albumname]
    - Since there's no MD5-Hashes for images either, the script simply uses the original filename to determine if it should download the image or not
4. Linux Server
    - Uses SSH to connect to the server
    - Archive
        - Uses `zip` on the server to compress, then backs up as many versions as specified
    - Non-archive
        - Uses `rsync`
5. MySQL Database
    - Uses `mysqldump` to dump the database
6. WordPress
    - Simply a combination of "Linux Server" and "MySQL Database"
7. Dropbox
    - Mirrors the folder structure of your Dropbox to your backup-path
	- Checks for content hash to determine whether to download it or not (to avoid overhead)
