"""Backup strategy for MongoDB."""

import subprocess

from helpers.strategy import Strategy

from helpers import util

class MongoDB(Strategy):
    """Backup strategy for MongoDB."""
    NAME = 'MongoDB'
    TYPE = 'mongodb'

    def start_backup(self):
        """
        Start backup.
        """
        # Download database
        self.download(self.config.get('db_name'), self.config.get('db_host'), self.config.get('db_port'), self.config.get('db_user'), self.config.get('db_pass'), self.backup_path)

    def download(self, db_name, db_host, db_port, db_user, db_pass, path_to):
        """
        Use mongodump to download dump.

        @param string db_name
        @param string db_host
        @param int db_port
        @param string db_user
        @param string db_pass
        @param string path_to
        """
        # Determine filename
        filename = self.alias + '_' + util.startup_time

        # Prepare dump command
        cmd = 'mongodump --forceTableScan -h {} --port {} --db {} --gzip --out {}/{}'.format(db_host, db_port, db_name, path_to, filename)

        if db_user and db_pass:
            cmd += ' --username {} --password "{}" --authenticationDatabase admin'.format(db_user, db_pass)

        try:
            subprocess.run([cmd], shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as err:
            raise Exception('Error downloading: {} STDOUT: {})'.format(err.stderr.decode('utf-8'), err.stdout.decode('utf-8'))) from err
