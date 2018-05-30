import os
import json
import requests
from urllib.parse import urlencode, quote_plus

class Google_Drive_Backup():
    GOOGLE_API = "https://www.googleapis.com/drive/v3/files"
    SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'
    ACCESS = 'offline'
    credentials = ''
    token = ''
    project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    module = 'googledrive'
    config = {}
    try_count = 0

    def __init__(self):
        self.config = self.read_config()
        self.credentials = self.read_credentials()
        self.token = self.read_token()

        if not self.credentials:
            print("No credentials found")
            return

        if not self.token:
            self.enable()

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

    def read_credentials(self):
        credentials_all = self.config_get('credentials', None)

        if credentials_all:
            return credentials_all['installed']

    def read_token(self):
        return self.config_get('token')

    def execute_request(self, url, headers={}, params={}, method="GET"):
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
            if self.try_count == 0:
                print("Token expired... Trying to get a new one")
                self.try_count = self.try_count + 1
                self.obtain_token()
            else:
                raise Exception("Failed to refresh token")

        return {'status': res.status_code, 'body': res.json()}

    def children(self, id='root', indentation=0):
        #print("Children for " + id)
        res = self.execute_request(self.GOOGLE_API + "?q='" + id + "'+in+parents&fields=files(id%2Cname%2Cmd5Checksum%2CmimeType)")
        items = res['body']['files']
        offset = ' ' * 4 * indentation

        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                print('{0}{1} | {2}'.format(offset, item['id'], item['name']))
                self.children(item['id'], indentation + 1)
            else:
                checksum = item['md5Checksum'] if 'md5Checksum' in item else ''
                print('{0}{1} | {2} -> {3}'.format(offset, item['id'], item['name'], checksum))

    def obtain_token(self, code=""):
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
        else:
            print("Error getting token: " + str(res['body']))

        print(res)

    def enable(self):
        # Build auth uri
        auth_uri = self.credentials['auth_uri'] + "?response_type=code" + "&redirect_uri=" + quote_plus(self.credentials['redirect_uris'][0]) + "&client_id=" + quote_plus(self.credentials['client_id']) + "&scope=" + quote_plus(self.SCOPES) + "&access_type=" + quote_plus(self.ACCESS) + "&approval_prompt=auto"

        print("Visit:")
        print(auth_uri)
        print("")

        code = input('Enter code: ')

        self.obtain_token(code)

gd = Google_Drive_Backup()
gd.children()
