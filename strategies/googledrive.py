"""Backup strategy for Google Drive."""

from helpers.strategy import Strategy
from helpers.cache import Cache
from helpers import util
import os
from datetime import datetime
import re
import json
import webbrowser
from urllib.parse import quote_plus
import requests
import urllib3
from pathlib import Path


# Prevent SSL certificate errors
from urllib3.contrib import pyopenssl
pyopenssl.extract_from_urllib3()


class GoogleDrive(Strategy):
    """Backup strategy for Google Drive."""
    NAME = 'Google Drive'
    TYPE = 'googledrive'
    API_URL = 'https://www.googleapis.com/drive/v3/files'
    cache = None

    def add(self):
        """Add Google Drive account."""
        self.alias = super().add()

        # Show instructions
        self.show_instructions()

        # Parse credentials
        credentials_str = input('Paste content of credentials file: ')
        self.config.set('credentials', json.loads(
            credentials_str)['installed'])

        # Get access code
        code = self.request_code()
        token = self.request_token(code)

        self.config.set('token', token)

    def start_backup(self):
        """Start backup."""
        # Set cache
        self.cache = Cache(self.alias)

        # Backup
        self.get_children()

        # Cleanup
        self.cleanup()

    def cleanup(self):
        """Delete files that have been removed from Drive."""
        all_cached = self.cache.get()

        for id, item in list(all_cached.items()):
            if item['last_seen'] is not util.startup_time and 'path' in item:
                # Delete file
                Path(item['path']).unlink(missing_ok=True)

                # Remove item from cache
                self.cache.delete(id)

    def build_auth_uri(self):
        """Build auth URI for requesting token.

        @return string
        """
        auth_uri = self.config.get('credentials.auth_uri')
        auth_uri += '?response_type=code'
        auth_uri += '&redirect_uri=' + \
            quote_plus(self.config.get('credentials.redirect_uris.0'))
        auth_uri += '&client_id=' + \
            quote_plus(self.config.get('credentials.client_id'))
        auth_uri += '&scope=https://www.googleapis.com/auth/drive.readonly'
        auth_uri += '&access_type=offline'
        auth_uri += '&approval_prompt=auto'

        return auth_uri

    def request_code(self):
        """Request code from auth URI to obtain token.

        @return string
        """
        # Build auth uri
        auth_uri = self.build_auth_uri()

        # Try opening in browser
        webbrowser.open(auth_uri, new=1)

        print()
        print('If your browser does not open, go to this website:')
        print(auth_uri)
        print()

        # Return code
        return input('Enter code: ')

    def execute_request(self, url, headers={}, params={}, method='GET', is_retry=False):
        """Call Drive API.

        @param string url
        @param dict headers
        @param dict params
        @param string method
        @param bool is_retry
        """
        if self.config.get('token.access_token'):
            # Set Authorization-Header
            auth_header = {
                'Authorization': 'Bearer {}'.format(self.config.get('token.access_token'))
            }
            headers.update(auth_header)

        # Execute request
        if method == 'GET':
            res = requests.get(url, headers=headers, params=params)
        else:
            res = requests.post(url, headers=headers, data=params)

        # Permission error
        if res.status_code == 401:
            # Maybe the token is expired
            if not is_retry:
                # Refresh token
                self.config.set('token', self.request_token())

                # Re-try request
                return self.execute_request(url, headers, params, method, True)
            else:
                # This is already a retry, don't try again
                raise Exception('Failed to refresh token')

        return {
            'status': res.status_code,
            'headers': res.headers,
            'body': res.json()
        }

    def request_token(self, code=''):
        """Request access token.

        @param string code (optional)
        @return dict
        """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        params = {
            'client_id': self.config.get('credentials')['client_id'],
            'client_secret': self.config.get('credentials')['client_secret'],
            'redirect_uri': self.config.get('credentials')['redirect_uris'][0],
        }

        if code:
            params['grant_type'] = 'authorization_code'
            params['code'] = code
        else:
            params['grant_type'] = 'refresh_token'
            params['refresh_token'] = self.config.get('token')['refresh_token']

        res = self.execute_request(self.config.get('credentials')[
                                   'token_uri'], headers, params, 'POST')

        if res['status'] == 200:
            if self.config.get('token'):
                res['body']['refresh_token'] = self.config.get('token')[
                    'refresh_token']

            self.config.set('token', res['body'])
            return res['body']
        else:
            raise Exception('Error getting token: ' + str(res['body']))

    def show_instructions(self):
        """Print instructions on how to set up Google Cloud Project."""
        print()
        print('If you already have an OAuth-Client-ID, download the JSON')
        print('Otherwise, here\'s how to get credentials:')
        print('1. Go to https://console.developers.google.com/')
        print('2. Choose or create a project')
        print('3. Activate Photos API here: https://console.developers.google.com/apis/library/photoslibrary.googleapis.com')
        print('4. Open https://console.developers.google.com/apis/credentials/consent')
        print('5. Choose "External"')
        print('6. Enter a name, support email and contact email')
        print('7. Click "Save and continue"')
        print('8. Click "Add or remove scopes"')
        print('9. Select ".../auth/drive.readonly"')
        print('10. Select ".../auth/photoslibrary.readonly"')
        print('11. Click "Save and continue"')
        print('12. Enter yourself as a test user')
        print('13. Click "Save and continue"')
        print(
            '14. [Open credentials page](https://console.developers.google.com/apis/credentials)')
        print('15. Click on "Create Credentials" -> OAuth-Client-ID -> Desktop Application')
        print('16. Download the Client ID JSON')
        print()

    def check_if_excluded(self, path):
        """Check if file is to be excluded from download.

        @param string path
        @return boolean
        """
        for pattern in self.config.get('exclude'):
            if re.match(pattern, path):
                return True

        return False

    def is_folder(self, item):
        """Check if item is a Google Folder.

        @param GoogleDriveFile item
        @return boolean
        """
        return item['mimeType'] == 'application/vnd.google-apps.folder'

    def is_google_doc(self, item):
        """Check if item is a Google Doc.

        @param GoogleDriveFile item
        @return boolean
        """
        return item['mimeType'] == 'application/vnd.google-apps.document'

    def is_google_sheet(self, item):
        """Check if item is a Google Spreadsheet.

        @param GoogleDriveFile item
        @return boolean
        """
        return item['mimeType'] == 'application/vnd.google-apps.spreadsheet'

    def is_google_slides(self, item):
        """Check if item is a Google Slidedeck.

        @param GoogleDriveFile item
        @return boolean
        """
        return item['mimeType'] == 'application/vnd.google-apps.presentation'

    def get_children(self, item_id='root', parents=[], page_token=''):
        """Traverse Drive recursively and initiate file download.

        @param string item_id (optional)
        @param list parents (optional)
        @param string page_token (optional)
        """
        path_server = '/' + '/'.join(parents).strip('/')
        path = os.path.join(self.backup_path, path_server.strip('/'))

        params = {
            'q': "'" + item_id + "' in parents",
            'fields': 'nextPageToken,files(id,name,mimeType,modifiedTime,trashed)',
            'pageSize': '100'
        }

        if page_token:
            params['pageToken'] = page_token

        # Build param-string
        params_str = ''

        for key, param in params.items():
            params_str = params_str + key + '=' + param + '&'

        params_str = params_str[:-1].replace(',', '%2C').replace(' ', '+')

        # Send request
        res = self.execute_request(self.API_URL + '?' + params_str)

        items = res['body']['files'] if res['status'] == 200 else []

        for item in items:
            url = self.API_URL + '/' + item['id'] + '?alt=media'
            path_item = os.path.join(path_server, item['name'])
            filename = item['name']

            # Excluded or trashed
            if self.check_if_excluded(path_item):
                continue

            if item['trashed']:
                continue

            # Folders
            if self.is_folder(item):
                self.get_children(item['id'], parents + [item['name']])
                continue

            # Google Docs
            if self.is_google_doc(item):
                url = self.API_URL + '/' + \
                    item['id'] + '/export?mimeType=application/pdf'
                filename = item['name'] + '_converted.pdf'
            # Google Spreadsheets
            elif self.is_google_sheet(item):
                url = self.API_URL + '/' + \
                    item['id'] + '/export?mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                filename = item['name'] + '.xlsx'
            # Google Slides
            elif self.is_google_slides(item):
                url = self.API_URL + '/' + \
                    item['id'] + '/export?mimeType=application/pdf'
                filename = item['name'] + '_converted.pdf'

            # Remember last seen in cache
            self.cache.set(item['id'] + '.last_seen', util.startup_time)

            # Move if moved
            if self.check_if_moved_and_move(item, path, filename):
                continue

            # Download
            if not self.is_backed_up(item, path, filename):
                try:
                    self.download(url, path, filename)

                    # Add to cache
                    self.cache.set(item['id'] + '.modified',
                                   item['modifiedTime'])
                    self.cache.set(item['id'] + '.path',
                                   os.path.join(path, filename))
                except Exception as e:
                    self.logger.error(e)

        if 'nextPageToken' in res['body']:
            self.get_children(item_id, parents, res['body']['nextPageToken'])

    def check_if_moved_and_move(self, item, path, filename):
        """Check if source was simply moved and move if so.
        To determine whether the item has moved check the modified time.
        We can't use 'md5Checksum' here, because Google Docs don't have one.

        @param GoogleDriveFile item
        @param string path
        @param string filename
        @return boolean
        """
        move_source = self.cache.get(item['id'])

        if move_source and 'modified' in move_source:
            move_target = os.path.join(path, filename)

            if move_source['modified'] == item['modifiedTime'] \
                    and move_source['path'] != move_target:

                # Create folder if not exists
                if not os.path.exists(path):
                    os.makedirs(path)

                self.logger.info('Moving {} to {}'.format(
                    move_source['path'], move_target))
                os.rename(move_source['path'], move_target)

                self.cache.set(item['id'] + '.' + 'path', move_target)

                return True

        return False

    def is_backed_up(self, item, path, filename):
        """Check if file exists and is newer than on Drive.

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

    def download(self, url, path, filename):
        """Download item.

        @param string url
        @param string path
        @param string filename
        """
        # Create folder if not exists
        if not os.path.exists(path):
            os.makedirs(path)

        headers = {
            'Authorization': 'Bearer {}'.format(self.config.get('token')['access_token'])
        }

        # Download file
        self.logger.info('Downloading {}...'.format(
            os.path.join(path, filename)))

        http = urllib3.PoolManager()
        res = http.request('GET', url, headers=headers, preload_content=False)

        if res.status == 200:
            self.logger.info('Downloaded.')

            with open(os.path.join(path, filename), 'wb') as out:
                while True:
                    data = res.read(128)
                    if not data:
                        break
                    out.write(data)

            res.release_conn()
        else:
            raise Exception(
                'Download failed ({}) -> {}'.format(res.status, str(res.data)))
