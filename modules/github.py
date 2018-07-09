import requests
import getpass
import urllib.request
from urllib.parse import urlencode, quote_plus
import urllib3
import shutil
import base64
import json
import os
import re

from . import util

class Github_Backup:
    username = ""
    token = ""
    backup_path = ''
    GITHUB_API = "https://api.github.com"
    config = {}
    project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    module = 'github'
    backup_path = ''

    def __init__(self):
        self.config = self.read_config()
        self.backup_path = self.get_backup_path()

    def get_backup_path(self):
        backup_path = self.config_get('backup_path', 'backups/' + self.module)

        if not backup_path.startswith("/"):
            backup_path = self.project_path + "/" + backup_path

        if not os.path.exists(backup_path):
            os.makedirs(backup_path)

        return backup_path

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

    def get_token(self):
        util.log("Getting token...")
        password = getpass.getpass('Github password (' + self.username + '): ')

        res = requests.post(self.GITHUB_API + "/authorizations", auth = (self.username, password), data = json.dumps({'note': 'backup', 'note_url': 'backup_my_accounts'}))

        if res.status_code == 201:
            return res.json()['token']

        raise Exception("Error obtaining token: " + str(res.json()))

    def backup(self):
        util.log("")
        util.log("### Backup Github ###")
        util.log("")

        try:
            self.username = self.config_get('username')
            self.token = self.config_get('token')

            if not self.username:
                self.username = input('Github username: ')
                self.config_set('username', self.username)

            if not self.token:
                self.token = self.get_token()
                self.config_set('token', self.token)

            repositories = self.get_repositories()

            for repository in repositories:
                version = self.get_current_version(repository)

                self.download(version['url'], repository['name'], self.backup_path, repository['name'] + "-" + version['number'] + ".zip", True)

            util.log("Finished Github backup")

        except Exception as e:
            util.log(e)

    def get_repositories(self, page_url=""):
        repositories = []
        url = page_url if page_url else self.GITHUB_API + "/users/" + self.username + "/repos"
        res = requests.get(url, auth=(self.username,self.token))

        if res.status_code == 200:
            for repository in res.json():
                repositories.append(repository)

        if 'Link' in res.headers and res.headers['Link'].find('rel="next"') != -1:
            page_url = re.search('<(.*?)>', res.headers['Link']).group(1)
            repositories.extend(self.get_repositories(page_url))

        return repositories

    def get_current_version(self, repository):
        res = requests.get(repository['tags_url'], auth=(self.username,self.token)).json()

        version = res[0]['name'] if len(res) > 0 and 'name' in res[0] else '1.0'
        url = res[0]['zipball_url'] if len(res) > 0 and 'zipball_url' in res[0] else "https://github.com/" + self.username + "/" + repository['name'] + "/archive/master.zip"

        return {'number': version, 'url': url}

    def get_current_tag(self, repository):
        tags = requests.get(repository['tags_url'], auth=(self.username, self.token)).json()

        return tags[0]['name'] if len(tags) > 0 and 'name' in tags[0] else '1.0'

    def delete_older_versions(self, path, repo_name):
        for f in os.listdir(path):
            if re.search('^' + repo_name + '-[0-9.]+zip', f):
                os.remove(os.path.join(self.backup_path, f))

    def download(self, url, repo_name, path, filename, check_if_exists=False):
        # Check if file exists
        if check_if_exists and os.path.isfile(os.path.join(path, filename)):
            return

        # Delete older version
        self.delete_older_versions(path, repo_name)

        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self.username, self.token)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opener = urllib.request.build_opener(authhandler)
        urllib.request.install_opener(opener)

        util.log(os.path.basename(filename))

        with urllib.request.urlopen(url) as response, open(os.path.join(path, filename), 'wb') as out_file:
            data = response.read()
            out_file.write(data)

if __name__ == "__main__":
    g = Github_Backup()
    g.backup()
