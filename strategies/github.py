"""Backup strategy for GitHub."""

import os
import re
import subprocess
import urllib.request
import requests

from helpers.strategy import Strategy

class Github(Strategy):
    """Backup strategy for GitHub."""
    NAME = 'GitHub'
    TYPE = 'github'
    API_URL = 'https://api.github.com'

    def start_backup(self):
        """
        Start backup.
        """
        # Get all repositories
        repositories = self.get_repositories()

        for repository in repositories:
            if self.config.get('archive'):
                self.archive(repository, True)
            else:
                self.sync(repository)

    def get_repositories(self, page_url=''):
        """
        Get all repositories.

        @param string page_url (optional)
        @return list
        """
        repositories = []
        url = page_url if page_url else '{api_url}/users/{username}/repos'.format(api_url=self.API_URL, username=self.config.get('username'))
        res = requests.get(url, auth=(self.config.get('username'), self.config.get('token')))

        if res.status_code == 200:
            for repository in res.json():
                repositories.append(repository)

        next_page_url = self.get_next_page_url(res.headers)

        if next_page_url:
            repositories.extend(self.get_repositories(next_page_url))

        return repositories

    def get_next_page_url(self, headers):
        """
        Get next page URL.

        @param dict headers
        @return string
        """
        if 'Link' in headers and headers['Link'].find('rel="next"') != -1:
            return re.search(r'<([^;]+)>; rel=\"next\"', headers['Link']).group(1)

        return None

    def get_current_version(self, repository):
        """
        Get current repository version from latest tag.

        @param dict repository
        @return dict
        """
        res = requests.get(repository['tags_url'], auth=(self.config.get('username'), self.config.get('token'))).json()

        version = res[0]['name'] if len(res) > 0 and 'name' in res[0] else None
        url = res[0]['zipball_url'] if len(res) > 0 and 'zipball_url' in res[0] else 'https://github.com/{}/{}/archive/{}.zip'.format(self.config.get('username'), repository['name'], repository['default_branch'])

        return {'number': version, 'url': url}

    def get_current_tag(self, repository):
        """
        Get lastest tag from repository.

        @param string repository
        @return string
        """
        tags = requests.get(repository['tags_url'], auth=(self.config.get('username'), self.config.get('token'))).json()

        return tags[0]['name'] if len(tags) > 0 and 'name' in tags[0] else '1.0'

    def delete_older_versions(self, path, repo_name):
        """
        Remove older version of repository.

        @param string path
        @param string repo_name
        """
        for f in os.listdir(path):
            if re.search('^' + repo_name + '-[0-9.]+zip', f):
                os.remove(os.path.join(self.backup_path, f))

    def archive(self, repository, check_if_exists=False):
        """
        Download repository as zip file.

        @param dict repository
        @param boolean check_if_exists (optional)
        """
        # Get current version
        version = self.get_current_version(repository)
        
        # Determine version suffix
        suffix = '-' + version['number'] if version['number'] else ''

        # Determine filename
        filename = repository['name'] + '-' + suffix + '.zip'

        # Check if file exists
        if check_if_exists and os.path.isfile(os.path.join(self.backup_path, filename)):
            return

        # Get URL
        url = version['url']

        # Delete older version
        self.delete_older_versions(self.backup_path, repository['name'])

        # Actually download the file
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self.config.get('username'), self.config.get('token'))
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opener = urllib.request.build_opener(authhandler)
        urllib.request.install_opener(opener)

        self.logger.info('Archiving {} ({})...'.format(repository['name'], version['number']))

        try:
            with urllib.request.urlopen(url) as response, open(os.path.join(self.backup_path, filename), 'wb') as out_file:
                data = response.read()
                out_file.write(data)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                self.logger.error('URL {} not found (404)'.format(url))

    def sync(self, repository):
        """
        Clone or pull repository.

        @param dict repository
        """
        # Get current version
        version = self.get_current_version(repository)

        try:
            if os.path.exists(os.path.join(self.backup_path, repository['name'])):
                self.logger.info('Pulling {} ({})...'.format(repository['name'], version['number']))
                subprocess.run(['git', '-C', os.path.join(self.backup_path, repository['name']), 'pull', '--rebase', repository['clone_url']], check=True, capture_output=True)
            else:
                self.logger.info('Cloning {} ({})...'.format(repository['name'], version['number']))
                subprocess.run(['git', '-C', self.backup_path, 'clone', repository['clone_url']], check=True, capture_output=True)
        except subprocess.CalledProcessError as err:
            self.logger.error('Error synchronizing repo: {} STDOUT: {})'.format(err.stderr.decode('utf-8'), err.stdout.decode('utf-8')))
