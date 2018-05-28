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
    token_path = 'tokens/github'
    GITHUB_API = "https://api.github.com"

    def get_token(self):
        print("Getting token...")
        password = getpass.getpass('Github password: ')

        res = requests.post(self.GITHUB_API + "/authorizations", auth = (self.username, password), data = json.dumps({'note': 'backup', 'note_url': 'backup_my_accounts'}))

        if res.status_code == 201:
            print("Token obtained")

            self.token = res.json()['token']

            with open(self.token_path, 'w') as f:
                f.write(self.token)

            return True
        else:
            print("Error obtaining token: " + str(res.json()))
            return False

    def backup(self):
        if not self.username:
            self.username = input('Github username: ')

        if not os.path.isfile(self.token_path):
            if not self.get_token():
                return
        else:
            with open(self.token_path, 'r') as f:
                self.token = f.read()

        repositories = self.get_repositories()

        for repository in repositories:
            tag = self.get_current_tag(repository)

            print(repository + " -> " + tag)

            #self.download(self.GITHUB_API + self.username + "/repository + "/archive/master.zip", repository + "-" + tag + ".zip")
            return

    def get_repositories(self):
        print("Getting repositories")
        repositories = []
        res = requests.get(self.GITHUB_API + "/users/" + self.username + "/repos", auth=(self.username,self.token))

        if res.status_code == 200:
            for repository in res.json():
                repositories.append(repository['name'])

        return repositories

    def get_current_tag(self, repository):
        tags = requests.get(self.GITHUB_API + "/repos/" + self.username + "/" + repository + "/tags", auth=(self.username,self.token)).json()

        return tags[0]['name'] if len(tags) > 0 and 'name' in tags[0] else '1.0'

    def download_file(self, url, filename):
        print("Download " + filename)
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
        passman.add_password(None, url, self.username, self.password)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opener = urllib.request.build_opener(authhandler)
        urllib.request.install_opener(opener)

        with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
            data = response.read()
            out_file.write(data)

g = Github_Backup()
g.backup()
