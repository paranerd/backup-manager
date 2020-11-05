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
import subprocess

from helpers import util
from helpers import config
from helpers.log import Logger

class Github_Backup:
    name = "GitHub"
    type = "github"
    username = ""
    token = ""
    API_URL = "https://api.github.com"
    backup_path = ""

    def __init__(self):
        """
        Constructor
        """
        self.logger = Logger()

    def add(self):
        """
        Add GitHub account
        """
        # Read alias
        alias = input('Alias: ')

        # Check if alias exists
        while config.exists(alias):
            print("This alias already exists")
            alias = input('Alias: ')

        # Read username
        username = input('GitHub username: ')

        # Read password
        password = getpass.getpass('GitHub password: ')

        # Read backup path
        backup_path = input('Backup path (optional): ') or 'backups/' + alias

        # Read archive choice
        archive = input("Archive? [y/N]: ")
        archive = archive != None and archive.lower() == 'y'

        try:
            # Obtain token
            token = self.get_token(username, password)
        except Exception as e:
            raise Exception("Could not obtain access token. Please check your credentials. {}".format(e))

        # Write config
        config.set(alias, 'type', self.type)
        config.set(alias, 'username', username)
        config.set(alias, 'token', token)
        config.set(alias, 'backup_path', backup_path)
        config.set(alias, 'archive', archive)

        print("Added.")

    def backup(self, alias):
        """
        Main worker

        @param string alias
        """
        self.logger.write("")
        self.logger.write("### Backup {} ({}) ###".format(alias, self.name))
        self.logger.write("")

        if not config.exists(alias):
            self.logger.write("Alias {} does not exist".format(alias))
            return

        try:
            self.username = config.get(alias, 'username')
            self.token = config.get(alias, 'token')
            self.backup_path = config.get(alias, 'backup_path')
            do_archive = config.get(alias, 'archive')

            # Make sure backup path exists
            util.create_backup_path(self.backup_path, alias)

            if not self.username or not self.token:
                raise Exception("Username and/or Token not set")

            # Get all repositories
            repositories = self.get_repositories()

            for repository in repositories:
                self.logger.addToBuffer(repository['name'])

                if do_archive:
                    self.archive(repository, True)
                else:
                    self.sync(repository)
                self.logger.flush()

            self.logger.write("Finished GitHub backup")

        except Exception as e:
            self.logger.flush()
            self.logger.write(e)

    def sync(self, repository):
        """
        Clone or pull repository

        @param dict repository
        """
        if os.path.exists(os.path.join(self.backup_path, repository['name'])):
            self.logger.addToBuffer(" -> Pulling...")
            subprocess.run(['git', '-C', os.path.join(self.backup_path, repository['name']), "pull", "--rebase", "https://github.com/paranerd/{}.git".format(repository['name'])], stdout=subprocess.PIPE)
        else:
            self.logger.addToBuffer(" -> Cloning...")
            subprocess.run(['git', '-C', self.backup_path, "clone", "https://github.com/paranerd/{}.git".format(repository['name'])], stdout=subprocess.PIPE)

    def get_token(self, username, password):
        """
        Get auth token

        @param string username
        @param string password
        @return string
        """
        print("Getting token...")

        res = requests.post(self.API_URL + "/authorizations", auth = (username, password), data = json.dumps({'note': 'backup_debug', 'note_url': 'backup_my_accounts_debug'}))

        if res.status_code != 201:
            raise Exception("Error obtaining token: " + str(res.json()))

        return res.json()['token']

    def get_repositories(self, page_url=""):
        """
        Get all repositories

        @param string page_url
        @return list
        """
        repositories = []
        url = page_url if page_url else self.API_URL + "/users/" + self.username + "/repos"
        res = requests.get(url, auth=(self.username,self.token))

        if res.status_code == 200:
            for repository in res.json():
                repositories.append(repository)

        if 'Link' in res.headers and res.headers['Link'].find('rel="next"') != -1:
            page_url = re.search('\<([^;]+)\>; rel=\"next\"', res.headers['Link']).group(1)
            repositories.extend(self.get_repositories(page_url))

        return repositories

    def get_current_version(self, repository):
        """
        Get current repository version from latest tag

        @param dict repository
        @return dict
        """
        res = requests.get(repository['tags_url'], auth=(self.username,self.token)).json()

        version = res[0]['name'] if len(res) > 0 and 'name' in res[0] else '1.0'
        url = res[0]['zipball_url'] if len(res) > 0 and 'zipball_url' in res[0] else "https://github.com/" + self.username + "/" + repository['name'] + "/archive/master.zip"

        return {'number': version, 'url': url}

    def get_current_tag(self, repository):
        """
        Get lastest tag from repository

        @param string repository
        @return string
        """
        tags = requests.get(repository['tags_url'], auth=(self.username, self.token)).json()

        return tags[0]['name'] if len(tags) > 0 and 'name' in tags[0] else '1.0'

    def delete_older_versions(self, path, repo_name):
        """
        Remove older version of repository

        @param string path
        @param string repo_name
        """
        for f in os.listdir(path):
            if re.search('^' + repo_name + '-[0-9.]+zip', f):
                os.remove(os.path.join(self.backup_path, f))

    def archive(self, repository, check_if_exists=False):
        """
        Download repository as zip file

        @param dict repository
        @param string check_if_exists
        """
        # Check if file exists
        if check_if_exists and os.path.isfile(os.path.join(self.backup_path, repository['name'])):
            return

        # Get current version
        version = self.get_current_version(repository)

        # Get URL
        url = version['url']

        # Determine filename
        filename = repository['name'] + "-" + version['number'] + ".zip"

        # Delete older version
        self.delete_older_versions(self.backup_path, repository['name'])

        # Actually download the file
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self.username, self.token)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opener = urllib.request.build_opener(authhandler)
        urllib.request.install_opener(opener)

        self.logger.addToBuffer(" -> " + os.path.basename(filename))

        with urllib.request.urlopen(url) as response, open(os.path.join(self.backup_path, filename), 'wb') as out_file:
            data = response.read()
            out_file.write(data)
