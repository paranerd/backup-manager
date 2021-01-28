import os
import json
import re
import getpass
import subprocess
import urllib.request
import requests
import hashlib
from pathlib import Path

import shutil

from helpers import util
from helpers import config
from helpers.log import Logger

class GithubGist:
    NAME = "GitHub Gist"
    TYPE = "github-gist"
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

            # Get all gists
            gists = self.get_gists()

            for gist in gists:
                if do_archive:
                    self.archive(gist, True)
                else:
                    self.sync(gist)

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

    def get_gists(self, page_url=""):
        """
        Get all gists

        @param string page_url
        @return list
        """
        gists = []
        url = page_url if page_url else "{api_url}/users/{username}/gists".format(api_url=self.API_URL, username=self.username)
        res = requests.get(url, auth=(self.username, self.token))

        if res.status_code == 200:
            for gist in res.json():
                gists.append(gist)

        next_page_token = self.get_next_page_url(res.headers)

        if next_page_token:
            gists.extend(self.get_gists(next_page_token))

        return gists

    def get_next_page_url(self, headers):
        """
        Gets next page url from headers

        @param dict headers
        @return string
        """
        if 'Link' in headers and headers['Link'].find('rel="next"') != -1:
            return re.search('\<([^;]+)\>; rel=\"next\"', headers['Link']).group(1)

        return None

    def get_current_version(self, gist):
        """
        Gets current gist version from from update datetime

        @param dict gist
        @return dict
        """
        return hashlib.sha1(gist['updated_at'].encode("UTF-8")).hexdigest()[:10]

    def delete_older_versions(self, path, gist_name):
        """
        Remove older version of gist

        @param string path
        @param string gist_name
        """
        for f in os.listdir(path):
            if re.search('^' + gist_name + '-.*\.zip', f):
                os.remove(os.path.join(self.backup_path, f))

    def archive(self, gist, check_if_exists=False):
        """
        Download gist as zip file

        @param dict gist
        @param string check_if_exists
        """
        self.logger.info("Archiving {}...".format(gist['id']))

        # Get current version
        version = self.get_current_version(gist)

        # Create temporary folder
        tmp_path = util.create_tmp_folder()

        # Determine destination filename
        first_filename = next(iter(gist['files']))
        first_filename, _ = os.path.splitext(first_filename)
        destination = os.path.join(self.backup_path, gist['id'] + "-" + first_filename + "-" + version)

        # Check if file exists
        if check_if_exists and os.path.isfile(destination + ".zip"):
            self.logger.info("{} is up-to-date".format(gist['id']))
            return

        # Delete older version
        self.delete_older_versions(self.backup_path, gist['id'])

        # Download every file in the gist to tmp
        for file in gist['files']:
            self.download(gist['files'][file]['raw_url'], tmp_path, gist['files'][file]['filename'])

        # Create archive from tmp
        shutil.make_archive(destination, 'zip', tmp_path)

    def sync(self, gist):
        """
        Clone or pull gist

        @param dict gist
        """
        # Get current version
        version = self.get_current_version(gist)

        try:
            if os.path.exists(os.path.join(self.backup_path, gist['id'])):
                self.logger.info("Pulling {} ({})...".format(gist['id'], version))
                subprocess.run(['git', '-C', os.path.join(self.backup_path, gist['id']), "pull", "--rebase", gist['git_pull_url']], check=True, capture_output=True)
            else:
                self.logger.info("Cloning {} ({})...".format(gist['id'], version))
                subprocess.run(['git', '-C', self.backup_path, "clone", gist['git_pull_url']], check=True, capture_output=True)
        except subprocess.CalledProcessError as err:
            self.logger.error("Error synchronizing gist: {} STDOUT: {})".format(err.stderr.decode('utf-8'), err.stdout.decode('utf-8')))

    def download(self, url, path, filename):
        """
        Downloads gist file to temporary folder

        @param string url
        @param string path
        @param string filename
        """
        # Prepare urllib
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self.username, self.token)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opener = urllib.request.build_opener(authhandler)
        urllib.request.install_opener(opener)

        # Actually download the file
        with urllib.request.urlopen(url) as response, open(os.path.join(path, filename), 'wb') as out_file:
            data = response.read()
            out_file.write(data)