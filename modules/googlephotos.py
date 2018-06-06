import os
import re
import json
import requests
import webbrowser
from urllib.parse import urlencode, quote_plus
import urllib3

class Google_Photos_Backup():
    GOOGLE_API = "https://photoslibrary.googleapis.com/v1"
    SCOPES = 'https://www.googleapis.com/auth/photoslibrary'
    ACCESS = 'offline'
    credentials = ''
    token = ''
    project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    backup_path = ''
    module = 'googlephotos'
    config = {}

    def __init__(self):
        self.config = self.read_config()
        self.credentials = self.config_get('credentials', None)
        self.token = self.config_get('token')
        self.backup_path = self.get_backup_path()

    def get_backup_path(self):
        backup_path = self.config_get('backup_path', 'backups/' + self.module)

        if not backup_path.startswith("/"):
            backup_path = self.project_path + "/" + backup_path

        if not os.path.exists(backup_path):
            os.makedirs(backup_path)

        return backup_path

    def request_credentials(self):
        credentials_str = input('Paste credentials: ')
        print("")
        self.credentials = json.loads(credentials_str)['installed']

        self.config_set('credentials', self.credentials)

    def request_code(self):
        # Build auth uri
        auth_uri = self.credentials['auth_uri'] + "?response_type=code" + "&redirect_uri=" + quote_plus(self.credentials['redirect_uris'][0]) + "&client_id=" + quote_plus(self.credentials['client_id']) + "&scope=" + quote_plus(self.SCOPES) + "&access_type=" + quote_plus(self.ACCESS) + "&approval_prompt=auto"

        webbrowser.open(auth_uri, new=2)

        print("If your browser does not open, go to this website:")
        print(auth_uri)
        print("")

        code = input('Enter code: ')

        self.token = self.request_token(code)

    def read_config(self):
        with open(self.project_path + '/config.json', 'r') as f:
            return json.load(f)

    def config_get(self, key, default=""):
        if not self.module in self.config:
            self.config[self.module] = {}
            self.write_config()

        return self.config[self.module][key] if key in self.config[self.module] and self.config[self.module][key] != "" else default

    def config_set(self, key, value):
        self.config[self.module][key] = value
        self.write_config()

    def write_config(self):
        with open(self.project_path + '/config.json', 'w') as f:
            f.write(json.dumps(self.config, indent=4))

    def execute_request(self, url, headers={}, params={}, method="GET", retry=False):
        if "access_token" in self.token:
            # Set Authorization-Header
            auth_header = {
                'Authorization': 'Bearer {}'.format(self.token['access_token'])
            }
            headers.update(auth_header)

        # Execute request
        if method == 'GET':
            res = requests.get(url, headers=headers)
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

    def backup(self):
        if not self.credentials:
            self.request_credentials()

        if not self.token:
            self.request_code()

        albums = self.get_albums()

        for album in albums:
            print(album['title'])
            self.get_album_contents(album['id'], album['title'])

    def get_albums(self):
        res = self.execute_request(self.GOOGLE_API + "/albums")

        return res['body']['albums']

    def get_album_contents(self, id, name, pageToken=""):
        params = {
            "pageSize": "100",
            "albumId": id
        }

        if pageToken:
            params['pageToken'] = pageToken

        res = self.execute_request(self.GOOGLE_API + "/mediaItems:search", {}, params, "POST")

        if 'mediaItems' in res['body']:
            items = res['body']['mediaItems']

            result = re.match('([0-9]{4})-', name)

            year = result.group(1) if result else '0000'

            for item in items:
                width = item['mediaMetadata']['width']
                height = item['mediaMetadata']['height']

                extension = item['mimeType'].split("/",1)[1]
                filename = re.sub("[^0-9]", "", item['mediaMetadata']['creationTime'])
                path = self.backup_path + "/" + year + "/" + name + "/" + filename[:8] + "_" + filename[8:] + "." + extension

                if not os.path.exists(path):
                    print("    Downloading " + path.replace(self.backup_path + "/", ""))
                    self.download(item['baseUrl'] + "=w" + width + "-h" + height, path)

        if 'nextPageToken' in res['body']:
            self.get_album_contents(id, name, res['body']['nextPageToken'])

    def download(self, url, path):
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        headers = {
            'Authorization': 'Bearer {}'.format(self.token['access_token'])
        }

        http = urllib3.PoolManager()
        r = http.request('GET', url, headers=headers, preload_content=False)

        with open(path, 'wb') as out:
            while True:
                data = r.read(128)
                if not data:
                    break
                out.write(data)

        r.release_conn()

    def create_album(self, name):
        params = {
            "album": {"title": name}
        }
        res = self.execute_request(self.GOOGLE_API + "/albums", {}, json.dumps(params), "POST")

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
            self.config_set('token', res['body'])
            return res['body']
        else:
            raise Exception("Error getting token: " + str(res['body']))

if __name__ == "__main__":
    gp = Google_Photos_Backup()
    gp.backup()
