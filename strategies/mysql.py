"""Backup strategy for MySQL."""

import subprocess
import re

from helpers.strategy import Strategy

from helpers import util

class MySQL(Strategy):
    """Backup strategy for MySQL."""
    NAME = 'MySQL'
    TYPE = 'mysql'

    def start_backup(self):
        """
        Start backup.
        """
        # Download database
        self.download(self.config.get('db_name'), self.config.get('db_host'), self.config.get('db_user'), self.config.get('db_pass'), self.backup_path, self.config.get('db_port'))

    def download(self, db_name, db_host, db_user, db_pass, path_to, db_port=3306):
        """
        Use mysqldump to dump MySQL database to file.

        @param string db_name
        @param string db_host
        @param string db_user
        @param string db_pass
        @param string path_to
        @param string db_port
        """
        # Sanitize password
        db_pass = re.escape(db_pass)

        # Determine filename
        filename = self.alias + '_' + util.startup_time

        try:
            # Dump MySQL
            cmd = 'mysqldump {} --column-statistics=0 --add-drop-table -h {} -P {} -u {} -p{} > {}/{}.sql'.format(db_name, db_host, db_port, db_user, db_pass, path_to, filename)
            subprocess.run([cmd], shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as err:
            raise Exception('Error dumping: {} STDOUT: {})'.format(err.stderr.decode('utf-8'), err.stdout.decode('utf-8'))) from err
