"""Backup strategy for PostgreSQL."""

import subprocess
import re

from helpers import util
from helpers.strategy import Strategy

class PostgreSQL(Strategy):
    """Backup strategy for PostgreSQL."""
    NAME = 'PostgreSQL'
    TYPE = 'postgresql'

    def start_backup(self):
        """
        Start backup.
        """
        # Download database
        self.download(self.config.get('db_name'), self.config.get('db_host'), self.config.get('db_port'), self.config.get('db_user'), self.config.get('db_pass'), self.backup_path)

    def download(self, db_name, db_host, db_port, db_user, db_pass, path_to):
        """
        Use pg_dump to dump PostgreSQL database to file.

        @param string db_name
        @param string db_host
        @param string db_port
        @param string db_user
        @param string db_pass
        @param string path_to
        """
        # Sanitize password
        db_pass = re.escape(db_pass)

        # Determine filename
        filename = self.alias + '_' + util.startup_time

        try:
            # Dump database using pg_dump
            cmd = 'pg_dump -Fc postgresql://{}:{}@{}:{}/{} -f {}/{}.dump'.format(db_user, db_pass, db_host, db_port, db_name, path_to, filename)

            subprocess.run([cmd], shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as err:
            raise Exception('Error dumping: {} STDOUT: {})'.format(err.stderr.decode('utf-8'), err.stdout.decode('utf-8'))) from err
