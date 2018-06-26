# Backup My Accounts

A backup-tool for multiple cloud-services

Using "raw" web-requests, no special libraries whatsoever to keep dependencies at a minimum

Currently supported:
- Github
- Google Drive
- Google Photos

While Github is working "out-of-the-box", Google will need some minor setting up, see below for details

## Prerequisites
```sh
sudo apt install python3, python3-urllib3
```

## Configuration

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

## Setup Google-Backup

1. Go to https://console.developers.google.com/
2. Create a project
3. On the left, choose "Credentials"
4. Create an OAuth-Client-ID for "Others"
5. Download the generated credentials json
6. When prompted by the script, paste the content of that json

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
