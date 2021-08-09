# Backup Manager

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
sudo apt install python3 python3-urllib3 sshpass mysql-client postgresql-client git
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

## Set up E-Mail notifications
Note that this feature will currently only work with Gmail

On first start the script will ask for Gmail credentials for notifications.

If you choose to enable this feature, enter your Gmail-Account as "Mail user" and an "App Password" as "Mail password".

Check out [this link](https://support.google.com/accounts/answer/185833) for how to obtain an app password.

## Set up Google-Backup
1. [Open google cloud console](https://console.developers.google.com/)
1. Choose or create a project
1. [Activate Drive API](https://console.developers.google.com/apis/library/drive.googleapis.com)
1. [Activate Photos API](https://console.developers.google.com/apis/library/photoslibrary.googleapis.com)
1. [Create consent page](https://console.developers.google.com/apis/credentials/consent)
1. Choose "External"
1. Enter a name, support email and contact email
1. Click "Save and continue"
1. Click "Add or remove scopes"
1. Select ".../auth/drive.readonly"
1. Select ".../auth/photoslibrary.readonly"
1. Click "Save and continue"
1. Enter yourself as a test user
1. Click "Save and continue"
1. [Open credentials page](https://console.developers.google.com/apis/credentials)
1. Click on "Create Credentials" -> OAuth-Client-ID -> Desktop Application
1. Download the Client ID JSON
1. When prompted by the script, paste the content of that json

## Set up Dropbox-Backup
1. [Open Dropbox developers page](https://www.dropbox.com/developers/apps)
1. Click "Create app"
1. Select "Dropbox API"
1. Select "Full Dropbox"
1. Give it a name
1. Click "Create app"
1. Under "Generated access token" click "Generate"
1. When prompted by the script, paste that token

## Set up GitHub-Backup
Follow [this documentation](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token#creating-a-token) to create your personal access token.

You will be prompted for it when adding a GitHub backup

## Using with Docker
Backup Manager also works in a Docker environment.

### Adding accounts
To add new accounts, run:

```
docker run -it -v "/path/to/backups:/app/backups" -v "/path/to/config/config.json:/app/config/config.json" paranerd/backup-manager-dev add
```

Then follow the adding process.

You may replace the backup path however you like, just remember to reflect it properly when adding.

### Running the backup
Analogous to adding, the backup command is as follows:
```
docker run -it -v "/path/to/backups:/app/backups" -v "/path/to/config/config.json:/app/config/config.json" paranerd/backup-manager-dev backup [alias1, alias2]
```

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
