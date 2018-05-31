import os
import json
import shutil
import requests
import urllib3
from urllib.parse import urlencode, quote_plus

import util

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
        self.credentials = self.config_get('credentials')
        self.token = self.config_get('token')
        self.backup_path = self.get_backup_path()

        if not self.credentials:
            self.request_credentials()

        if not self.token:
            self.request_code()

    def get_backup_path(self):
        backup_path = self.config_get('backup_path', 'backups/github')

        if not backup_path.startswith("/"):
            backup_path = self.project_path + "/" + backup_path

        if not os.path.exists(backup_path):
            os.makedirs(backup_path)

        return backup_path

    def request_credentials(self):
        credentials_str = input('Paste credentials: ')
        self.credentials = json.loads(credentials_str)['installed']

        self.config_set('credentials', self.credentials)

    def request_code(self):
        # Build auth uri
        auth_uri = self.credentials['auth_uri'] + "?response_type=code" + "&redirect_uri=" + quote_plus(self.credentials['redirect_uris'][0]) + "&client_id=" + quote_plus(self.credentials['client_id']) + "&scope=" + quote_plus(self.SCOPES) + "&access_type=" + quote_plus(self.ACCESS) + "&approval_prompt=auto"

        print("Visit:")
        print(auth_uri)
        print("")

        code = input('Enter code: ')

        self.token = self.request_token(code)

    def read_config(self):
        with open(self.project_path + '/config.json', 'r') as f:
            return json.load(f)

    def config_get(self, key, default=""):
        if not self.module in self.config:
            print("adding")
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
            self.config_set('token', res['body'])
            return res['body']
        else:
            raise Exception("Error getting token: " + str(res['body']))

    def children(self, id='root', parents=[]):
        print(parents)

        res = self.execute_request(self.GOOGLE_API + "?q='" + id + "'+in+parents&fields=files(id%2Cname%2Cmd5Checksum%2CmimeType)")
        items = res['body']['files']
        offset = ' ' * 4 * len(parents)

        for item in items:
            path = "/" + ("/".join(parents) + "/" + item['name']).strip("/")
            print(path)

            if item['mimeType'] == 'application/vnd.google-apps.folder':
                print('{0}{1} | {2}'.format(offset, item['id'], item['name']))
                self.children(item['id'], parents + [item['name']])
            else:
                checksum_server = item['md5Checksum'] if 'md5Checksum' in item else ''
                checksum_local = util.md5_file(self.backup_path + path)

                print(checksum_server + " | " + checksum_local)

                if not checksum_server or checksum_server != checksum_local:
                    self.download_urllib3(item['id'], path)
                #print('{0}{1} | {2} -> {3}'.format(offset, item['id'], item['name'], checksum))

    def download_urllib3(self, id, path):
        util.create_folder(os.path.dirname(path))

        http = urllib3.PoolManager()
        r = http.request('GET', 'https://www.googleapis.com/drive/v3/files/' + id + '?alt=media', headers={'Authorization': 'Bearer {}'.format(self.token['access_token'])}, preload_content=False)

        with open(path, 'wb') as out:
            while True:
                data = r.read(128)
                if not data:
                    break
                out.write(data)

        r.release_conn()

    def download(self, id, path):
        print("download " + id)

        r = requests.get('https://www.googleapis.com/drive/v3/files/' + id + '?alt=media', headers={'Authorization': 'Bearer {}'.format(self.token['access_token'])})

        if r.status_code == 200:
            print("status 200")
            with open(path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print("status: " + str(r.status_code))
            print(r.json())

gd = Google_Drive_Backup()
gd.children()
