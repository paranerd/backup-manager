"""Backup strategy for Dropbox."""

import os
import re
import dropbox

from helpers.cache import Cache
from helpers.strategy import Strategy

class Dropbox(Strategy):
    """Backup strategy for Dropbox."""
    NAME = 'Dropbox'
    TYPE = 'dropbox'
    cache = None
    dbx = None

    def start_backup(self):
        """
        Start backup.
        """
        self.cache = Cache(self.alias)

        self.dbx = dropbox.Dropbox(self.config.get('token'))

        # Get files recursively
        self.get_children()

    def get_children(self, path=''):
        """
        Get items in directory.

        @param string path (optional)
        """
        res = self.dbx.files_list_folder(path=path)

        for entry in res.entries:
            if self.check_if_excluded(entry.path_display):
                continue
            elif isinstance(entry, dropbox.files.FolderMetadata):
                self.get_children(entry.path_display)
            else:
                destination = os.path.join(self.backup_path, entry.path_display.strip('/'))
                self.logger.info(entry.path_display)

                content_hash = self.cache.get(entry.path_display)

                if not os.path.isfile(destination) or content_hash != entry.content_hash:
                    self.cache.set(entry.path_display, entry.content_hash)
                    self.download(entry.path_display, destination)

    def download(self, dropbox_path, destination):
        """
        Download file.

        @param string dropbox_path
        @param string destination
        """
        parent = os.path.dirname(destination)

        if not os.path.exists(parent):
            os.makedirs(parent)

        with open(destination, 'wb+') as fout:
            _metadata, res = self.dbx.files_download(path=dropbox_path)
            fout.write(res.content)

    def check_if_excluded(self, path):
        """
        Check if path is excluded.

        @param string path
        @return boolean
        """
        for pattern in self.config.get('exclude'):
            if re.match(pattern, path):
                return True

        return False
