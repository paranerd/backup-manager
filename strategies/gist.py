"""Backup strategy for GitHub Gists."""

import os
import re
import subprocess
import urllib.request
import hashlib
import shutil
import requests

from helpers import util
from helpers.strategy import Strategy

class Gist(Strategy):
    """Backup strategy for GitHub Gists."""
    NAME = 'Gist'
    TYPE = 'gist'
    API_URL = 'https://api.github.com'

    def start_backup(self):
        """
        Start backup.
        """
        # Get all gists
        gists = self.get_gists()

        for gist in gists:
            if self.config.get('archive'):
                self.archive(gist, True)
            else:
                self.sync(gist)

    def get_gists(self, page_url=''):
        """
        Get all gists.

        @param string page_url (optional)
        @return list
        """
        gists = []
        url = page_url if page_url else '{api_url}/users/{username}/gists'.format(api_url=self.API_URL, username=self.config.get('username'))
        res = requests.get(url, auth=(self.config.get('username'), self.config.get('token')))

        if res.status_code == 200:
            for gist in res.json():
                gists.append(gist)

        next_page_token = self.get_next_page_url(res.headers)

        if next_page_token:
            gists.extend(self.get_gists(next_page_token))

        return gists

    def get_next_page_url(self, headers):
        """
        Get next page url from headers.

        @param dict headers
        @return string
        """
        if 'Link' in headers and headers['Link'].find('rel="next"') != -1:
            return re.search(r'<([^;]+)>; rel=\"next\"', headers['Link']).group(1)

        return None

    def get_current_version(self, gist):
        """
        Get current gist version from from update datetime.

        @param dict gist
        @return dict
        """
        return hashlib.sha1(gist['updated_at'].encode('UTF-8')).hexdigest()[:10]

    def delete_older_versions(self, path, gist_name):
        """
        Remove older version of gist.

        @param string path
        @param string gist_name
        """
        for filename in os.listdir(path):
            if re.search('^' + gist_name + r'-.*\.zip', filename):
                os.remove(os.path.join(self.backup_path, filename))

    def archive(self, gist, check_if_exists=False):
        """
        Download gist as zip file.

        @param dict gist
        @param string check_if_exists (optional)
        """
        self.logger.info('Archiving {}...'.format(gist['id']))

        # Get current version
        version = self.get_current_version(gist)

        # Create temporary folder
        tmp_path = util.create_tmp_folder()

        # Determine destination filename
        first_filename = next(iter(gist['files']))
        first_filename, _ = os.path.splitext(first_filename)
        destination = os.path.join(self.backup_path, gist['id'] + '-' + first_filename + '-' + version)

        # Check if file exists
        if check_if_exists and os.path.isfile(destination + '.zip'):
            self.logger.info('{} is up-to-date'.format(gist['id']))
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
        Clone or pull gist.

        @param dict gist
        """
        # Get current version
        version = self.get_current_version(gist)

        try:
            if os.path.exists(os.path.join(self.backup_path, gist['id'])):
                self.logger.info('Pulling {} ({})...'.format(gist['id'], version))
                subprocess.run(['git', '-C', os.path.join(self.backup_path, gist['id']), 'pull', '--rebase', gist['git_pull_url']], check=True, capture_output=True)
            else:
                self.logger.info('Cloning {} ({})...'.format(gist['id'], version))
                subprocess.run(['git', '-C', self.backup_path, 'clone', gist['git_pull_url']], check=True, capture_output=True)
        except subprocess.CalledProcessError as err:
            self.logger.error('Error synchronizing gist: {} STDOUT: {})'.format(err.stderr.decode('utf-8'), err.stdout.decode('utf-8')))

    def download(self, url, path, filename):
        """
        Download gist file to temporary folder.

        @param string url
        @param string path
        @param string filename
        """
        # Prepare urllib
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self.config.get('username'), self.config.get('token'))
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opener = urllib.request.build_opener(authhandler)
        urllib.request.install_opener(opener)

        # Actually download the file
        with urllib.request.urlopen(url) as response, open(os.path.join(path, filename), 'wb') as out_file:
            data = response.read()
            out_file.write(data)
