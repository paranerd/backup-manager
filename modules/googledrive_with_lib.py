# sudo pip3 install --upgrade google-api-python-client

from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import re

class Google_Drive_Backup:
    # Setup the Drive v3 API
    SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'
    store = file.Storage('credentials.json')
    creds = store.get()
    service = None

    def __init__(self):
        if not self.creds or self.creds.invalid:
            flow = client.flow_from_clientsecrets('client_secret.json', self.SCOPES)
            creds = tools.run_flow(flow, store.store)

        self.service = build('drive', 'v3', http=self.creds.authorize(Http()))

    def children(self, id=0):
        # Call the Drive v3 API
        results = self.service.files().list(q="'" + str(id) + "'" + " in parents", fields="files(id, name, md5Checksum, mimeType)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
        else:
            print('Files:')
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    print('{0} | {1}'.format(item['id'], item['name']))
                else:
                    print('{0} | {1} -> {2}'.format(item['id'], item['name'], item['md5Checksum']))

gd = Google_Drive_Backup()
gd.children("root")
gd.children("0B_ioiMhvJVphVjBQalJTOEhPU0k")
#children("root")
