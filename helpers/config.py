"""Config helper."""

import os
import json

from . import util

class ConfigHelper:
    """Config helper."""
    def __init__(self, namespace='', write_through=True, location=None):
        """
        Constructor

        @param string namespace (optional)
        @param boolean write_through (optional)
        """
        # Determine config location
        self.location = location or os.path.join(util.get_project_path(), 'config', 'config.json')

        # Set namespace
        self.namespace = namespace

        # Set write mode
        self.write_through = write_through

        # Read config to variable
        self.config = self.read()

    def set_write_through(self, status):
        """
        Update write through status.

        @param boolean status
        """
        self.write_through = status

    def read(self):
        """
        Read and return config file.

        @return dict
        """
        if os.path.exists(self.location):
            # Load config
            with open(self.location, 'r') as fin:
                return json.load(fin)
        else:
            # Return empty config
            return {}

    def exists(self, path=''):
        """
        Check if key exists in entry.

        @param string key (optional)
        @return boolean
        """
        obj = self.get(path)

        return obj is not None

    def get(self, path='', default=None):
        """
        Get config object at path.

        @param string path (optional)
        @param string default (optional)
        @return any
        """
        obj = self.config

        # Get path as list
        path_list = self.__get_absolute_path(path)

        # Get first list element
        elem = path_list.pop(0) if len(path_list) > 0 else None

        while elem:
            try:
                elem = int(elem) if elem.isnumeric() else elem
                obj = obj[elem]
                elem = path_list.pop(0) if len(path_list) > 0 else None
            except Exception:
                return default

        return obj

    def __get_absolute_path(self, path):
        """
        Return absolute path including any namespace.

        @param string path
        @return list
        """
        # Determine absolute path
        abs_path = '.'.join((self.namespace, path)).lstrip('.')

        # Convert to list
        path_list = abs_path.split('.')

        # Remove empty elements
        return list(filter(None, path_list))

    def __create_path(self, path):
        """
        Create path in config.

        @param string path
        """
        # Get absolute path
        path_list = self.__get_absolute_path(path)

        config = self.config

        for part in path_list:
            if part not in config:
                config[part] = {}
                config = config[part]

    def set(self, path, value):
        """
        Add value to config at path.

        @param string path
        @param string value
        """
        path_list = path.split('.')
        last = path_list.pop()

        self.__create_path('.'.join(path_list))

        obj = self.get('.'.join(path_list))

        if obj is not None:
            obj[last] = value

            if self.write_through:
                self.write()

    def write(self):
        """
        Write config to file.
        """
        with open(self.location, 'w') as fout:
            fout.write(json.dumps(self.config, indent=4))

    def delete(self, path):
        """
        Delete entry from config.

        @param string path
        """
        path_list = path.split('.')
        last = path_list.pop()

        obj = self.get('.'.join(path_list))

        if obj is not None:
            del obj[last]
            self.write()
