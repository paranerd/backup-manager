"""Backup strategy for Google Photos."""

import os
import re
import json
from urllib.parse import quote_plus
import webbrowser
import requests
import urllib3

# Prevent SSL certificate errors
from urllib3.contrib import pyopenssl
pyopenssl.extract_from_urllib3()

from helpers.cache import Cache
from helpers.strategy import Strategy

class GooglePhotos(Strategy):
    """Backup strategy for Google Photos."""
    NAME = 'Google Photos'
    TYPE = 'googlephotos'
    API_URL = 'https://photoslibrary.googleapis.com/v1'
    cache = None

    def add(self, override={}):
        """
        Add Google Photos account.

        @param dict override (optional)
        """
        self.alias = super().add()

        if not self.alias:
            return

        # Show instructions
        self.show_instructions()

        credentials_str = input('Paste content of credentials file: ')
        self.config.set('credentials', json.loads(credentials_str)['installed'])

        code = self.request_code()
        token = self.request_token(code)

        # Write config
        self.config.set('token', token)

    def start_backup(self):
        """
        Start backup.
        """
        self.logger.info('Getting albums...')

        # Set cache
        self.cache = Cache(self.alias)

        # Get all albums
        albums = self.get_albums()

        # Backup albums
        for album in albums:
            if not self.check_if_excluded(album['title']):
                self.logger.info('Scanning {} for new items...'.format(album['title']))
                self.get_album_content(album['id'], album['title'])

    def show_instructions(self):
        """
        Print instructions on how to set up Google Cloud Project.
        """
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
        print('8. Click "Add or remove scopes")
        print('9. Select ".../auth/drive.readonly")
        print('10. Select ".../auth/photoslibrary.readonly")
        print('11. Click "Save and continue")
        print('12. Enter yourself as a test user)
        print('13. Click "Save and continue")
        print('14. [Open credentials page](https://console.developers.google.com/apis/credentials))
        print('15. Click on "Create Credentials" -> OAuth-Client-ID -> Desktop Application)
        print('16. Download the Client ID JSON)
        print()

    def build_auth_uri(self):
        """
        Build auth URI for requesting token.

        @return string
        """
        auth_uri = self.config.get('credentials.auth_uri')
        auth_uri += '?response_type=code'
        auth_uri += '&redirect_uri=' + quote_plus(self.config.get('credentials.redirect_uris.0'))
        auth_uri += '&client_id=' + quote_plus(self.config.get('credentials.client_id'))
        auth_uri += '&scope=https://www.googleapis.com/auth/photoslibrary.readonly'
        auth_uri += '&access_type=offline'
        auth_uri += '&approval_prompt=auto'

        return auth_uri

    def request_code(self):
        """
        Request code from auth URI to obtain token.

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
        """
        Call Photos API.

        @param string url
        @param dict headers (optional)
        @param dict params (optional)
        @param string method (optional)
        @param bool is_retry (optional)
        """
        if 'access_token' in self.config.get('token', {}):
            # Set Authorization-Header
            auth_header = {
                'Authorization': 'Bearer {}'.format(self.config.get('token.access_token'))
            }
            headers.update(auth_header)

        # Execute request
        if method == 'GET':
            res = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            res = requests.post(url, headers=headers, data=params)
        elif method == 'HEAD':
            res = requests.head(url, headers=headers)

        # Permission error
        if res.status_code == 401:
            # Maybe the token is expired
            if not is_retry:
                # Refresh token
                self.config.set('token', self.request_token())

                # Re-try request
                return self.execute_request(url, headers, params, method, True)

            # This is already a retry, don't try again
            raise Exception('Failed to refresh token')

        body = res.json() if method != 'HEAD' else None

        return {
            'status': res.status_code,
            'headers': res.headers,
            'body': body
        }

    def check_if_excluded(self, name):
        """
        Check if album is to be excluded.

        @param string name
        @return string
        """
        for pattern in self.config.get('exclude'):
            if re.match(pattern, name):
                return True

        return False

    def get_albums(self, page_token=''):
        """
        Get all albums.

        @param string page_token (optional)
        @return dict
        """
        params = {
            'pageSize': '50',
        }

        if page_token:
            params['pageToken'] = page_token

        res = self.execute_request(self.API_URL + '/albums', {}, params)

        albums = res['body']['albums']

        if 'nextPageToken' in res['body']:
            albums.extend(self.get_albums(res['body']['nextPageToken']))

        return albums

    def get_album_content(self, album_id, name, page_token=''):
        """
        Get all items of an album and initializes download.

        @param string album_id
        @param string name
        @param string page_token (optional)
        """
        params = {
            'pageSize': '100',
            'albumId': album_id
        }

        if page_token:
            params['pageToken'] = page_token

        res = self.execute_request(self.API_URL + '/mediaItems:search', {}, params, 'POST')

        if 'mediaItems' in res['body']:
            items = res['body']['mediaItems']

            result = re.match('([0-9]{4})-', name)

            year = result.group(1) if result else '0000'

            for item in items:
                path = self.backup_path + '/' + year + '/' + name
                filename = self.cache.get(item['id'])
                url_postfix = '=dv' if 'video' in item['mediaMetadata'] else '=w' + item['mediaMetadata']['width'] + '-h' + item['mediaMetadata']['height']

                if 'video' in item['mediaMetadata']:
                    filename = filename if filename else self.get_video_filename(item)

                self.download(item['baseUrl'] + url_postfix, item['id'], path, filename)

        if 'nextPageToken' in res['body']:
            self.get_album_content(album_id, name, res['body']['nextPageToken'])

    def get_video_filename(self, item):
        """
        Determine filename of a video by issuing a HEAD request.

        @param dict item
        @return string
        """
        res = self.execute_request(item['baseUrl'], {}, {}, 'HEAD')

        filename = re.search('"(.*?)"', res['headers']['Content-Disposition']).group(1)
        filename, _ = os.path.splitext(filename)

        return filename + '.mp4'

    def download(self, url, item_id, path, filename=''):
        """
        Download item.

        @param string url
        @param string item_id
        @param string path
        @param string filename (optional)
        """
        # Create folder if not exists
        if not os.path.exists(path):
            os.makedirs(path)

        headers = {
            'Authorization': 'Bearer {}'.format(self.config.get('token')['access_token'])
        }

        # Check if file already exists
        if filename:
            if os.path.isfile(os.path.join(path, filename)):
                return
        else:
            res = self.execute_request(url, {}, {}, 'HEAD')

            if res['status'] != 200:
                self.logger.warn('Could not get file info ({}) -> {}'.format(str(res['status']), str(res['headers'])))
                return

            filename = re.search('"(.*?)"', res['headers']['Content-Disposition']).group(1)

            if os.path.isfile(os.path.join(path, filename)):
                self.cache.set(item_id, filename)
                return

        # Download file
        http = urllib3.PoolManager()
        res = http.request('GET', url, headers=headers, preload_content=False)

        if res.status == 200:
            filename = filename if filename else re.search('"(.*?)"',
                                                    res.headers['Content-Disposition']).group(1)
            self.cache.set(item_id, filename)
            self.logger.info('Downloading {} -> {}'.format(os.path.basename(path), filename))

            with open(os.path.join(path, filename), 'wb') as out:
                while True:
                    data = res.read(128)
                    if not data:
                        break
                    out.write(data)

            res.release_conn()
        else:
            self.logger.error('Error downloading ({}) -> {}'.format(str(res.status), str(res.data)))

    def create_album(self, name):
        """
        Create album.

        @param string name
        """
        params = {
            'album': {'title': name}
        }

        self.execute_request(self.API_URL + '/albums', {}, json.dumps(params), 'POST')

    def request_token(self, code=''):
        """
        Request auth token.

        @param string code
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

        res = self.execute_request(self.config.get('credentials')['token_uri'], headers, params, 'POST')

        if res['status'] == 200:
            if self.config.get('token'):
                res['body']['refresh_token'] = self.config.get('token')['refresh_token']

            self.config.set('token', res['body'])
            return res['body']

        raise Exception('Error getting token: ' + str(res['body']))
