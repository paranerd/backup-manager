"""Backup strategy for WordPress."""

from helpers.config import ConfigHelper
from helpers.strategy import Strategy

from .mysql import MySQL
from .server import Server

class Wordpress(Strategy):
    """Backup strategy for WordPress."""
    NAME = 'WordPress'
    TYPE = 'wordpress'

    def __init__(self):
        super().__init__()
        self.server = Server().set_logger(self.logger)
        self.mysql = MySQL().set_logger(self.logger)

    def add(self, override={}):
        """
        Add WordPress strategy.

        @param dict override (optional)
        """
        alias = self.server.add({'archive': True, 'type': self.TYPE})

        server_config = ConfigHelper(alias)

        override = {
            'alias': alias,
            'versions': server_config.get('versions')
        }

        self.mysql.add(override)

    def start_backup(self):
        """
        Start backup.
        """
        # Backup database
        self.mysql.backup(self.alias, True)

        # Backup files
        self.server.backup(self.alias, True)
