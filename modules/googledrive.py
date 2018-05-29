import json
import requests

class Google_Drive_Backup():
    GOOGLE_API = "https://www.googleapis.com/drive/v3/files"
    token = ''

    def __init__(self):
        self.token = self.read_token()

    def read_token(self):
        credentials = ''

        with open('credentials.json', 'r') as f:
            credentials = json.load(f)

        return credentials['access_token']

    def execute_request(self, url, headers={}, params={}, method="GET"):
        auth_header = {
            'Authorization': 'Bearer {}'.format(self.token)
            #'Authorization': "Bearer " + str(self.token)
        }

        headers.update(auth_header)

        res = requests.get(url, headers=auth_header)

        return {'status': res.status_code, 'body': res.json()}

    def children(self, id=0):
        print(self.token)
        #children = self.execute_request(self.GOOGLE_API)
        #print(children)
        #return

        headers = {
            'Authorization': 'Bearer {}'.format(self.token)
            #'Authorization': "Bearer " + str(self.token)
        }

        res = requests.get(self.GOOGLE_API, headers=headers)

        print(res.json())

gd = Google_Drive_Backup()
gd.children()
