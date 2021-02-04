import os
from datetime import datetime
import re
import json
import requests
import webbrowser
import urllib3
from urllib.parse import urlencode, quote_plus

# Prevent SSL certificate errors
from urllib3.contrib import pyopenssl
pyopenssl.extract_from_urllib3()

from helpers import util
from helpers import config
from helpers.log import Logger

class GoogleDrive():
    NAME = "Google Drive"
    TYPE = "googledrive"
    API_URL = "https://www.googleapis.com/drive/v3/files"
    credentials = ''
    token = ''
    backup_path = ''
    alias = ''
    exclude = []

    def __init__(self):
        self.logger = Logger()

    def add(self):
        # Read alias
        self.alias = input('Alias: ')

        # Check if alias exists
        while config.exists(self.alias):
            print("This alias already exists")
            self.alias = input('Alias: ')

        # Show instructions
        self.show_instructions()

        credentials_str = input('Paste content of credentials file: ')
        self.credentials = json.loads(credentials_str)['installed']

        code = self.request_code()
        token = self.request_token(code)

        # Read backup path
        backup_path = input('Backup path (optional): ') or 'backups/' + self.alias

        config.set(self.alias, 'type', self.TYPE)
        config.set(self.alias, 'credentials', self.credentials)
        config.set(self.alias, 'token', token)
        config.set(self.alias, 'backup_path', backup_path)

        print("Added.")

    def backup(self, alias):
        self.logger.set_source(alias)
        self.logger.info("Starting...")

        if not config.exists(alias):
            self.logger.error("Alias {} does not exist".format(alias))
            return

        self.alias = alias
        self.backup_path = config.get(alias, 'backup_path')
        self.credentials = config.get(alias, 'credentials', None)
        self.token = config.get(alias, 'token')
        self.exclude = config.get(alias, 'exclude') or []

        # Make sure backup path exists
        util.create_backup_path(self.backup_path, alias)

        try:
            self.get_children()

            # Done
            self.logger.info("Done")
        except KeyboardInterrupt:
            self.logger.warn("Interrupted")
        except Exception as e:
            self.logger.error(e)
        finally:
            return {
                'errors': self.logger.count_errors(),
                'warnings': self.logger.count_warnings()
            }

    def build_auth_uri(self):
        auth_uri = self.credentials['auth_uri']
        auth_uri += "?response_type=code"
        auth_uri += "&redirect_uri=" + quote_plus(self.credentials['redirect_uris'][0])
        auth_uri += "&client_id=" + quote_plus(self.credentials['client_id'])
        auth_uri += "&scope=https://www.googleapis.com/auth/drive.readonly"
        auth_uri += "&access_type=offline"
        auth_uri += "&approval_prompt=auto"

        return auth_uri

    def request_code(self):
        # Build auth uri
        auth_uri = self.build_auth_uri()

        # Try opening in browser
        webbrowser.open(auth_uri, new=2)

        print()
        print("If your browser does not open, go to this website:")
        print(auth_uri)
        print()

        # Return code
        return input('Enter code: ')

    def execute_request(self, url, headers={}, params={}, method="GET", retry=False):
        if "access_token" in self.token:
            # Set Authorization-Header
            auth_header = {
                'Authorization': 'Bearer {}'.format(self.token['access_token'])
            }
            headers.update(auth_header)

        # Execute request
        if method == 'GET':
            res = requests.get(url, headers=headers, params=params)
        else:
            res = requests.post(url, headers=headers, data=params)

        if res.status_code == 401:
            # Token expired
            if not retry:
                self.token = self.request_token()
                return self.execute_request(url, headers, params, method, True)
            else:
                raise Exception("Failed to refresh token")

        return {'status': res.status_code, 'body': res.json()}

    def request_token(self, code=""):
        if not self.credentials:
            raise Exception('Could not read credentials')

        if not code and not self.token:
            raise Exception('Could not read token')

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        params = {
            'client_id' 	: self.credentials['client_id'],
            'client_secret'	: self.credentials['client_secret'],
            'redirect_uri'	: self.credentials['redirect_uris'][0],
        }

        if code:
            params['grant_type'] = 'authorization_code'
            params['code'] = code
        else:
            params['grant_type'] = 'refresh_token'
            params['refresh_token'] = self.token['refresh_token']

        res = self.execute_request(self.credentials['token_uri'], headers, params, "POST")

        if res['status'] == 200:
            if self.token:
                res['body']['refresh_token'] = self.token['refresh_token']

            config.set(self.alias, 'token', res['body'])
            return res['body']
        else:
            raise Exception("Error getting token: " + str(res['body']))

    def show_instructions(self):
        """
        Prints setup instructions
        """
        print()
        print('If you already have an OAuth-Client-ID, download the JSON')
        print('Otherwise, here\'s how to get credentials:')
        print('1. Go to https://console.developers.google.com/')
        print('2. Choose or create a project')
        print('3. Activate Drive API here: https://console.developers.google.com/apis/library/drive.googleapis.com')
        print('4. Open https://console.developers.google.com/apis/credentials/consent')
        print('5. Choose "External"')
        print('6. Enter a name and click "Save"')
        print('7. Open https://console.developers.google.com/apis/credentials')
        print('8. Click on "Create Credentials" -> OAuth-Client-ID -> Desktop Application')
        print('9. Ignore the pop-up')
        print('10. Download the client ID JSON')
        print()

    def check_if_excluded(self, path):
        """
        Check if file is to be excluded from download.

        @param string path

        @return boolean
        """
        for pattern in self.exclude:
            if re.match(pattern, path):
                return True

        return False

    def is_folder(self, item):
        """
        Checks if item is a Google Folder

        @param GoogleDriveFile

        @return boolean
        """
        return item['mimeType'] == 'application/vnd.google-apps.folder'

    def is_google_doc(self, item):
        """
        Checks if item is a Google Doc

        @param GoogleDriveFile

        @return boolean
        """
        return item['mimeType'] == 'application/vnd.google-apps.document'

    def is_google_sheet(self, item):
        """
        Checks if item is a Google Spreadsheet

        @param GoogleDriveFile

        @return boolean
        """
        return item['mimeType'] == 'application/vnd.google-apps.spreadsheet'

    def is_google_slides(self, item):
        """
        Checks if item is a Google Slidedeck

        @param GoogleDriveFile

        @return boolean
        """
        return item['mimeType'] == 'application/vnd.google-apps.presentation'

    def get_children(self, item_id='root', parents=[], pageToken=""):
        """
        Traverses Drive recursively and initiates file download

        @param string item_id
        @param list parents
        @param string pageToken
        """
        path_server = "/" + "/".join(parents).strip("/")
        path = os.path.join(self.backup_path, path_server.strip("/"))

        params = {
            "q": "'" + item_id + "' in parents",
            "fields": "nextPageToken,files(id,name,md5Checksum,mimeType,modifiedTime,trashed)",
            "pageSize": "100"
        }

        if pageToken:
            params['pageToken'] = pageToken

        # Build param-string
        params_str = ""

        for key, param in params.items():
            params_str = params_str + key + "=" + param + "&"

        params_str = params_str[:-1].replace(",", "%2C").replace(" ", "+")

        # Send request
        res = self.execute_request(self.API_URL + "?" + params_str)

        items = res['body']['files'] if res['status'] == 200 else []

        for item in items:
            url = self.API_URL + "/" + item['id'] + '?alt=media'
            path_item = os.path.join(path_server, item['name'])
            filename = item['name']

            # Excluded or trashed
            if self.check_if_excluded(path_item) or item['trashed']:
                self.logger.info("Excluding {}".format(path_item))

                if item['trashed']:
                    self.logger.info("... because it is trashed.")
                continue
            # Folders
            elif self.is_folder(item):
                self.get_children(item['id'], parents + [item['name']])
                continue
            # Google Docs
            elif self.is_google_doc(item):
                url = self.API_URL + "/" + item['id'] + "/export?mimeType=application/pdf"
                filename = item['name'] + "_converted.pdf"
            # Google Spreadsheets
            elif self.is_google_sheet(item):
                url = self.API_URL + "/" + item['id'] + "/export?mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                filename = item['name'] + ".xlsx"
            # Google Slides
            elif self.is_google_slides(item):
                url = self.API_URL + "/" + item['id'] + "/export?mimeType=application/pdf"
                filename = item['name'] + "_converted.pdf"

            # Download
            if not self.is_backed_up(item, path, filename):
                self.download(url, path, item, filename)

        if 'nextPageToken' in res['body']:
            self.get_children(item_id, parents, res['body']['nextPageToken'])

    def is_backed_up(self, item, path, filename):
        """
        Checks if file exists and is newer than on Drive

        @param GoogleDriveFile item
        @param string path
        @param string filename

        @return boolean
        """
        if os.path.isfile(os.path.join(path, filename)):
            mtime_ts = os.path.getmtime(os.path.join(path, filename))
            mtime_date = datetime.utcfromtimestamp(mtime_ts).isoformat()

            if item['modifiedTime'] < mtime_date:
                return True

        return False


    def download(self, url, path, item, filename=None):
        """
        Downloads item

        @param string url
        @param string path
        @param GoogleDriveFile
        @param string|None filename
        """
        # Create folder if not exists
        if not os.path.exists(path):
            os.makedirs(path)

        headers = {
            'Authorization': 'Bearer {}'.format(self.token['access_token'])
        }

        # Download file
        self.logger.info("Downloading {}...".format(os.path.join(path, filename)))

        http = urllib3.PoolManager()
        res = http.request('GET', url, headers=headers, preload_content=False)

        if res.status == 200:
            self.logger.info("Downloaded.")
            with open(os.path.join(path, filename), 'wb') as out:
                while True:
                    data = res.read(128)
                    if not data:
                        break
                    out.write(data)

            res.release_conn()
        else:
            self.logger.error("Download failed ({}) -> {}".format(res.status, str(res.data)))
