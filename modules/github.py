import requests
import getpass
import urllib.request
import shutil
import base64
import json
import os

class Github_Backup:
    username = ""
    token = ""
    backup_path = ''
    GITHUB_API = "https://api.github.com"
    config = {}
    project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    module = 'github'
    backup_path = 'backups/github'

    def __init__(self):
        self.config = self.read_config()
        self.backup_path = self.get_backup_path()

    def get_backup_path(self):
        backup_path = self.config_get('backup_path', self.backup_path)

        if not backup_path.startswith("/"):
            backup_path = self.project_path + "/" + backup_path

        if not os.path.exists(backup_path):
            os.makedirs(backup_path)

        return backup_path

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

    def get_token(self):
        print("Getting token...")
        password = getpass.getpass('Github password: ')

        res = requests.post(self.GITHUB_API + "/authorizations", auth = (self.username, password), data = json.dumps({'note': 'backup', 'note_url': 'backup_my_accounts'}))

        if res.status_code == 201:
            return res.json()['token']

        raise Exception("Error obtaining token: " + str(res.json()))

    def backup(self):
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

                path = self.backup_path + "/" + repository['name'] + "-" + version['number'] + ".zip"

                print(repository['name'] + " (" + version['number'] + ")", end="", flush=True)

                if (os.path.isfile(path)):
                    print(" -> Up-to-date")
                else:
                    print(" -> Downloading... ", end="", flush=True)
                    self.download(version['url'], path)
                    print(" Done.")
        except Exception as e:
            print(e)

    def get_repositories(self):
        repositories = []
        res = requests.get(self.GITHUB_API + "/users/" + self.username + "/repos", auth=(self.username,self.token))

        if res.status_code == 200:
            for repository in res.json():
                repositories.append(repository)

        return repositories

    def get_current_version(self, repository):
        res = requests.get(repository['tags_url'], auth=(self.username,self.token)).json()

        version = res[0]['name'] if len(res) > 0 and 'name' in res[0] else '1.0'
        url = res[0]['zipball_url'] if len(res) > 0 and 'zipball_url' in res[0] else "https://github.com/" + self.username + "/" + repository['name'] + "/archive/master.zip"

        return {'number': version, 'url': url}

    def get_current_tag(self, repository):
        tags = requests.get(repository['tags_url'], auth=(self.username, self.token)).json()

        return tags[0]['name'] if len(tags) > 0 and 'name' in tags[0] else '1.0'

    def download_file(self, url, filename):
        with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

    def get(self):
        try:
            res = urllib.request.urlopen(self.GITHUB_API + "/users/" + self.username + "/repos").read()
            repositories = json.loads(res.decode("utf-8") )

            for repository in repositories:
                print(repository['name'])

        except urllib.error.HTTPError as e:
            print(e.code)

    def download(self, url, filename):
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self.username, self.token)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opener = urllib.request.build_opener(authhandler)
        urllib.request.install_opener(opener)

        with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
            data = response.read()
            out_file.write(data)

g = Github_Backup()
g.backup()
