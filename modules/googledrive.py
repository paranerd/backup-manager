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

    def __init__(self):
        self.config = self.read_config()
        self.credentials = self.read_credentials()
        self.token = self.read_token()

    def read_config(self):
        with open(self.project_path + '/config.json', 'r') as f:
            return json.load(f)

    def config_get(self, key, default=""):
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
        # Encode URL
        url = quote_plus(url)

        # Set Authorization-Header
        auth_header = {
            'Authorization': 'Bearer {}'.format(self.token)
            #'Authorization': "Bearer " + str(self.token)
        }

        headers.update(auth_header)

        # Execute request
        if method == 'GET':
            res = requests.get(url, headers=headers)
        else:
            res = requests.post(url, headers=headers, data=params)

        return {'status': res.status_code, 'body': res.json()}

    def children(self, id='root'):
        res = requests.get(self.GOOGLE_API + "?q='" + str(id) + "' in parents&fields=files(id, name, md5Checksum, mimeType)")

        print(res.json())

    def refresh_token(self):
        if not self.credentials:
            raise Exception('Could not read credentials')

        if not self.token:
            raise Exception('Could not read token')

        params = {
          'client_id': self.credentials['client_id'],
          'client_secret': self.credentials['client_secret'],
          'refresh_token': self.token['refresh_token'],
          'grant_type': 'refresh_token'
        }
        '''
        $response = $this->execute_request($this->credentials['token_uri'], $header, http_build_query($params))
        if($response) {
            $access_token = $response['body']
            if ($access_token && array_key_exists('access_token', $access_token)) {
                $access_token['refresh_token'] = $this->token['refresh_token']
                $access_token['created'] = time()
                // Write access token
                return (file_put_contents($this->token_path, json_encode($access_token)) !== false)
            }
        }
        return false
        '''

    def create_auth_uri(self):
        if not self.credentials:
            raise Exception('Could not read credentials')

        return self.credentials['auth_uri'] + "?response_type=code" + "&redirect_uri=" + quote_plus(self.credentials['redirect_uris'][0]) + "&client_id=" + quote_plus(self.credentials['client_id']) + "&scope=" + quote_plus(self.SCOPES) + "&access_type=" + quote_plus(self.ACCESS) + "&approval_prompt=auto"

    def exchange_code_for_token(self, code):
        if not self.credentials:
            raise Exception('Could not read credentials')

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        params = {
            'code'			: code,
            'client_id' 	: self.credentials['client_id'],
            'client_secret'	: self.credentials['client_secret'],
            'redirect_uri'	: self.credentials['redirect_uris'][0],
            'grant_type'	: 'authorization_code'
        }

        res = self.execute_request(self.credentials['token_uri'], headers, params, "POST")

        if res['status'] == 200:
            print("Successful: " + str(res['body']))
            self.config_set('token', res['body'])
        else:
            print("Error getting token: " + res['body'])

        #self.credentials['token_uri']
        #client_id=GOOGLE_CLIENT_ID&client_secret=GOOGLE_CLIENT_SECRET&grant_type=authorization_code&code=AUTHORIZATION_CODE
        print(res)

    def enable(self):
        auth_uri = self.create_auth_uri()

        print("Visit:")
        print(auth_uri)
        print("")

        code = input('Code: ')

        self.exchange_code_for_token(code)

gd = Google_Drive_Backup()
#gd.enable()

gd.children()
#auth_url = gd.create_auth_url()
#print(auth_url)
#gd.exchange_code_for_token("4/AADCnBemUjKj0sbiQ14dUVMCtdW0y7TeVEnYjY3-KQCR_WqKUZESQSo")
