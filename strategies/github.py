import os
import json
import re
import getpass
import subprocess
import urllib.request
import requests

from helpers import util
from helpers import config
from helpers.log import Logger

class Github:
    NAME = "GitHub"
    TYPE = "github"
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

        # Read token
        token = getpass.getpass('GitHub token: ')

        # Read backup path
        backup_path = input('Backup path (optional): ') or 'backups/' + alias

        # Read archive choice
        archive = input("Archive? [y/N]: ")
        archive = archive != None and archive.lower() == 'y'

        # Write config
        config.set(alias, 'type', self.TYPE)
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
        self.logger.set_source(alias)
        self.logger.info("Starting...")

        if not config.exists(alias):
            self.logger.error("Alias {} does not exist".format(alias))
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
                if do_archive:
                    self.archive(repository, True)
                else:
                    self.sync(repository)

            # Done
            self.logger.info("Done")
        except KeyboardInterrupt:
            self.logger.warn("Interrupted")
        except Exception as e:
            self.logger.error(e)
        finally:
            return {
                'errors': self.logger.count_errors(),
                'warnings': self.logger.count_warnings()
            }

    def get_repositories(self, page_url=""):
        """
        Get all repositories

        @param string page_url
        @return list
        """
        repositories = []
        url = page_url if page_url else "{api_url}/users/{username}/repos".format(api_url=self.API_URL, username=self.username)
        res = requests.get(url, auth=(self.username, self.token))

        if res.status_code == 200:
            for repository in res.json():
                repositories.append(repository)

        next_page_token = self.get_next_page_url(res.headers)

        if next_page_token:
            repositories.extend(self.get_repositories(next_page_token))

        return repositories

    def get_next_page_url(self, headers):
        if 'Link' in headers and headers['Link'].find('rel="next"') != -1:
            return re.search('\<([^;]+)\>; rel=\"next\"', headers['Link']).group(1)

        return None

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
        # Get current version
        version = self.get_current_version(repository)

        # Determine filename
        filename = repository['name'] + "-" + version['number'] + ".zip"

        # Check if file exists
        if check_if_exists and os.path.isfile(os.path.join(self.backup_path, filename)):
            return

        # Get URL
        url = version['url']

        # Delete older version
        self.delete_older_versions(self.backup_path, repository['name'])

        # Actually download the file
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self.username, self.token)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opener = urllib.request.build_opener(authhandler)
        urllib.request.install_opener(opener)

        self.logger.info("Archiving {} ({})...".format(repository['name'], version['number']))

        with urllib.request.urlopen(url) as response, open(os.path.join(self.backup_path, filename), 'wb') as out_file:
            data = response.read()
            out_file.write(data)

    def sync(self, repository):
        """
        Clone or pull repository

        @param dict repository
        """
        # Get current version
        version = self.get_current_version(repository)

        try:
            if os.path.exists(os.path.join(self.backup_path, repository['name'])):
                self.logger.info("Pulling {} ({})...".format(repository['name'], version['number']))
                subprocess.run(['git', '-C', os.path.join(self.backup_path, repository['name']), "pull", "--rebase", repository['clone_url']], check=True, capture_output=True)
            else:
                self.logger.info("Cloning {} ({})...".format(repository['name'], version['number']))
                subprocess.run(['git', '-C', self.backup_path, "clone", repository['clone_url']], check=True, capture_output=True)
        except subprocess.CalledProcessError as err:
            self.logger.error("Error synchronizing repo: {} STDOUT: {})".format(err.stderr.decode('utf-8'), err.stdout.decode('utf-8')))