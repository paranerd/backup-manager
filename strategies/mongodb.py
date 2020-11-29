import subprocess
import datetime

from helpers import util
from helpers import config
from helpers.log import Logger

class MongoDB:
    NAME = "MongoDB"
    TYPE = "mongodb"

    def __init__(self):
        self.logger = Logger()

    def add(self):
        # Read alias
        alias = input('Alias: ')

        # Check if alias exists
        while config.exists(alias):
            print("This alias already exists")
            alias = input('Alias: ')

        backup_path = input('Backup path (optional): ') or 'backups/' + alias
        db_name = input("Database name: ")
        db_user = input("Database user: ")
        db_host = input("Database host: ")
        db_port = input("Database port [27017]: ") or 27017
        db_pass = input("Database password: ")

        config.set(alias, 'type', self.TYPE)
        config.set(alias, 'backup_path', backup_path)
        config.set(alias, 'db_name', db_name)
        config.set(alias, 'db_user', db_user)
        config.set(alias, 'db_host', db_host)
        config.set(alias, 'db_port', db_port)
        config.set(alias, 'db_pass', db_pass)

        print("Added.")

    def get_timestring(self):
        """
        Get current timestamp formatted as string

        @return string
        """
        return datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')

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

        filename = self.get_timestring()

        backup_path = config.get(alias, 'backup_path')
        db_name = config.get(alias, 'db_name')
        db_user = config.get(alias, 'db_user')
        db_host = config.get(alias, 'db_host')
        db_port = config.get(alias, 'db_port')
        db_pass = config.get(alias, 'db_pass')

        try:
            # Make sure backup path exists
            util.create_backup_path(backup_path, alias)

            # Download database
            self.download(db_name, db_host, db_port, db_user, db_pass, backup_path, filename)

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
        # Prepare dump command
        cmd = "mongodump --forceTableScan -h {} --port {} --db {} --gzip --out {}/{}".format(db_host, db_port, db_name, path_to, filename)

        if db_user and db_pass:
            cmd += " --username {} --password '{}' --authenticationDatabase admin".format(db_user, db_pass)

        try:
            subprocess.run([cmd], shell=True, check=True)
        except subprocess.CalledProcessError:
            self.logger.error("Error downloading")