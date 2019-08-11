# Backup My Accounts

A backup-tool for multiple cloud-services

Using "raw" web-requests, no special libraries whatsoever to keep dependencies at a minimum

Currently supported:
- Github
- Google Drive
- Google Photos
- WordPress

While Github is working "out-of-the-box", Google will need some minor setting up, see below for details

## Prerequisites
```sh
sudo apt install python3 python3-urllib3 sshpass
```

## Configuration
- Renaming config.json_sample to config.json
- Setting a backup path

    By default, files will be backed up to the backups/-folder within the project's root

    You can change this location by modifying the config.json as follows:

    ```python
    {
        "github": {
            "backup_path": "/path/to/your/backups"
        }
    }
    ```

## Setup E-Mail notifications
On first start the script will ask for GMail credentials for notifications.  
If you choose to enable this feature, enter your GMail-Account as "Mail user" and an "app password" as "Mail password".  
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
