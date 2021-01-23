import subprocess
import re
import datetime

from helpers import util
from helpers import config
from helpers.log import Logger

class PostgreSQL:
    NAME = "PostgreSQL"
    TYPE = "postgresql"

    def __init__(self):
        self.logger = Logger()

    def add(self):
        """
        Adds PostgreSQL entry to config
        """
        # Read alias
        alias = input('Alias: ')

        # Check if alias exists
        while config.exists(alias):
            print("This alias already exists")
            alias = input('Alias: ')

        backup_path = input('Backup path (optional): ') or 'backups/' + alias
        versions = input("Keep versions [1]: ") or 1
        db_name = input("Database name: ")
        db_user = input("Database user: ")
        db_host = input("Database host: ")
        db_port = input("Database port [5432]: ") or 5432
        db_pass = input("Database password: ")

        config.set(alias, 'type', self.TYPE)
        config.set(alias, 'backup_path', backup_path)
        config.set(alias, 'versions', int(versions))
        config.set(alias, 'db_name', db_name)
        config.set(alias, 'db_user', db_user)
        config.set(alias, 'db_host', db_host)
        config.set(alias, 'db_port', db_port)
        config.set(alias, 'db_pass', db_pass)

        print("Added.")

    def get_timestring(self):
        """
        Gets current timestamp formatted as string

        @return string
        """
        return datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')

    def backup(self, alias):
        """
        Starts backup

        @param string alias
        """
        self.logger.set_source(alias)
        self.logger.info("Starting...")

        if not config.exists(alias):
            self.logger.error("Alias {} does not exist".format(alias))
            return

        backup_path = config.get(alias, 'backup_path')
        versions = config.get(alias, 'versions')
        db_name = config.get(alias, 'db_name')
        db_user = config.get(alias, 'db_user')
        db_host = config.get(alias, 'db_host')
        db_port = config.get(alias, 'db_port')
        db_pass = config.get(alias, 'db_pass')

        try:
            # Make sure backup path exists
            util.create_backup_path(backup_path, alias)

            # Determine filename
            filename = alias if versions < 2 else alias + "_" + self.get_timestring()

            # Download database
            self.download(db_name, db_host, db_port, db_user, db_pass, backup_path, filename)

            # Remove old versions
            util.cleanup_versions(backup_path, versions, alias)

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

    def download(self, db_name, db_host, db_port, db_user, db_pass, path_to, filename):
        """
        Uses pg_dump to dump PostgreSQL database to file

        @param string db_name
        @param string db_host
        @param string db_port
        @param string db_user
        @param string db_pass
        @param string path_to
        @param string filename
        """
        # Sanitize password
        db_pass = re.escape(db_pass)

        try:
            # Dump database using pg_dump
            cmd = "pg_dump -Fc postgresql://{}:{}@{}:{}/{} -f {}/{}.dump".format(db_user, db_pass, db_host, db_port, db_name, path_to, filename)

            subprocess.run([cmd], shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as err:
            self.logger.error("Error dumping: {} STDOUT: {})".format(err.stderr.decode('utf-8'), err.stdout.decode('utf-8')))
