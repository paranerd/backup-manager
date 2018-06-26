import os
import re
import json
import requests
import webbrowser
import urllib3
from urllib.parse import urlencode, quote_plus

from . import util

class Google_Drive_Backup():
    GOOGLE_API = "https://www.googleapis.com/drive/v3/files"
    SCOPES = 'https://www.googleapis.com/auth/drive'
    ACCESS = 'offline'
    credentials = ''
    token = ''
    project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    backup_path = ''
    module = 'googledrive'
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
        util.log("")
        self.credentials = json.loads(credentials_str)['installed']

        self.config_set('credentials', self.credentials)

    def request_code(self):
        # Build auth uri
        auth_uri = self.credentials['auth_uri'] + "?response_type=code" + "&redirect_uri=" + quote_plus(self.credentials['redirect_uris'][0]) + "&client_id=" + quote_plus(self.credentials['client_id']) + "&scope=" + quote_plus(self.SCOPES) + "&access_type=" + quote_plus(self.ACCESS) + "&approval_prompt=auto"

        webbrowser.open(auth_uri, new=2)

        util.log("If your browser does not open, go to this website:")
        util.log(auth_uri)
        util.log("")

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

            self.config_set('token', res['body'])
            return res['body']
        else:
            raise Exception("Error getting token: " + str(res['body']))

    def backup(self):
        util.log("")
        util.log("### Backup Google Drive ###")
        util.log("")

        if not self.credentials:
            self.request_credentials()

        if not self.token:
            self.request_code()

        self.get_children()

        util.log("Finished Google Drive backup")

    def get_children(self, id='root', parents=[], pageToken=""):
        path = self.backup_path + "/" + "/".join(parents).strip("/")
        util.log("/" + ("/".join(parents)))

        params = {
            "q": "'" + id + "' in parents",
            "fields": "nextPageToken,files(id,name,md5Checksum,mimeType)",
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
        res = self.execute_request(self.GOOGLE_API + "?" + params_str)

        items = res['body']['files'] if res['status'] == 200 else []

        for item in items:
            # Folders
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                self.get_children(item['id'], parents + [item['name']])
            # Google Docs
            elif item['mimeType'] == 'application/vnd.google-apps.document':
                url = self.GOOGLE_API + "/" + item['id'] + "/export?mimeType=application/pdf"
                self.download(url, path, item['name'] + ".pdf", False)
            # Google Spreadsheets
            elif item['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                url = self.GOOGLE_API + "/" + item['id'] + "/export?mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                self.download(url, path, item['name'] + ".xlsx", False)
            # Regular files
            else:
                checksum_server = item['md5Checksum'] if 'md5Checksum' in item else ''
                checksum_local = util.md5_file(path)

                if not checksum_server or checksum_server != checksum_local:
                    url = self.GOOGLE_API + "/" + item['id'] + '?alt=media'
                    self.download(url, path, item['name'], False)

        if 'nextPageToken' in res['body']:
            self.get_children(id, parents, res['body']['nextPageToken'])

    def download(self, url, path, filename="", check_if_exists=False):
        # Create folder if not exists
        if not os.path.exists(path):
            os.makedirs(path)

        headers = {
            'Authorization': 'Bearer {}'.format(self.token['access_token'])
        }

        # Check if file already exists
        if check_if_exists:
            res = requests.head(url, headers=headers)

            if res.status_code != 200:
                raise Exception("Error getting file info")

            filename = filename if filename else re.search('"(.*?)"', res.headers['Content-Disposition']).group(1)

            if os.path.isfile(os.path.join(path, filename)):
                return

        # Download file
        http = urllib3.PoolManager()
        r = http.request('GET', url, headers=headers, preload_content=False)

        if r.status == 200:
            filename = filename if filename else re.search('"(.*?)"', r.headers['Content-Disposition']).group(1)
            util.log("    " + filename)

            with open(os.path.join(path, filename), 'wb') as out:
                while True:
                    data = r.read(128)
                    if not data:
                        break
                    out.write(data)

            r.release_conn()
        else:
            raise Exception("Error downloading")

if __name__ == "__main__":
    gd = Google_Drive_Backup()
    gd.backup()
