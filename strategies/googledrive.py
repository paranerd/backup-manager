import os
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

class Google_Drive_Backup():
	name = "Google Drive"
	type = "googledrive"
	API_URL = "https://www.googleapis.com/drive/v3/files"
	credentials = ''
	token = ''
	backup_path = ''
	alias = ''

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

		config.set(self.alias, 'type', 'googledrive')
		config.set(self.alias, 'credentials', self.credentials)
		config.set(self.alias, 'token', token)
		config.set(self.alias, 'backup_path', backup_path)

		print("Added.")

	def backup(self, alias):
		self.logger.write("")
		self.logger.write("### Backup {} (Google Drive) ###".format(alias))
		self.logger.write("")

		if not config.exists(alias):
			self.logger.write("Alias {} does not exist".format(alias))
			return

		self.alias = alias
		self.backup_path = config.get(alias, 'backup_path')
		self.credentials = config.get(alias, 'credentials', None)
		self.token = config.get(alias, 'token')
		self.exclude = config.get(alias, 'exclude', [])

		# Make sure backup path exists
		util.create_backup_path(self.backup_path, alias)

		try:
			self.get_children()

			self.logger.write("Finished Google Drive backup")
		except KeyboardInterrupt:
			self.logger.write("Interrupted")

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
		for e in self.exclude:
			if re.match(e, path):
				return True

		return False

	def is_type(self, item, type):
		if type == 'folder' and item['mimeType'] == 'application/vnd.google-apps.folder':
			return True
		elif type == 'document' and item['mimeType'] == 'application/vnd.google-apps.document':
			return True
		elif type == 'spreadsheet' and item['mimeType'] == 'application/vnd.google-apps.spreadsheet':
			return True
		else:
			return False

	def get_children(self, id='root', parents=[], pageToken=""):
		path_server = "/" + "/".join(parents).strip("/")
		path = os.path.join(self.backup_path, path_server.strip("/"))

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
		res = self.execute_request(self.API_URL + "?" + params_str)

		items = res['body']['files'] if res['status'] == 200 else []

		for item in items:
			path_item = os.path.join(path_server, item['name'])

			if self.check_if_excluded(path_item):
				self.logger.write(path_item + " | excluded")
				continue
			elif not self.is_type(item, 'folder'):
				self.logger.addToBuffer(path_item)

			# Folders
			if self.is_type(item, 'folder'):
				self.get_children(item['id'], parents + [item['name']])
			# Google Docs
			elif self.is_type(item, 'document'):
				url = self.API_URL + "/" + item['id'] + "/export?mimeType=application/pdf"
				self.download(url, path, item['name'] + "_converted.pdf", False)
			# Google Spreadsheets
			elif self.is_type(item, 'spreadsheet'):
				url = self.API_URL + "/" + item['id'] + "/export?mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
				self.download(url, path, item['name'] + ".xlsx", False)
			# Regular files
			else:
				checksum_server = item['md5Checksum'] if 'md5Checksum' in item else ''
				checksum_local = util.md5_file(os.path.join(path, item['name']))

				if not checksum_server or checksum_server != checksum_local:
					url = self.API_URL + "/" + item['id'] + '?alt=media'
					self.download(url, path, item['name'], False)

			self.logger.flush()

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
				self.logger.addToBuffer(" (Error getting file info)")
				return

			filename = filename if filename else re.search('"(.*?)"', res.headers['Content-Disposition']).group(1)

			if os.path.isfile(os.path.join(path, filename)):
				return

		# Download file
		http = urllib3.PoolManager()
		r = http.request('GET', url, headers=headers, preload_content=False)

		if r.status == 200:
			filename = filename if filename else re.search('"(.*?)"', r.headers['Content-Disposition']).group(1)

			with open(os.path.join(path, filename), 'wb') as out:
				while True:
					data = r.read(128)
					if not data:
						break
					out.write(data)

			r.release_conn()
		else:
			self.logger.addToBuffer(" (Error downloading: " + str(r.status) + " | " + str(r.data) + ")")
