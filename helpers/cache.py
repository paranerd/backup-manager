import os
import json

from . import util

class Cache:
    def __init__(self, namespace):
        """
        Constructor

        @param string namespace
        """
        self.namespace = namespace

        # Determine cache location
        self.location = os.path.join(util.get_project_path(), "cache", "{}.json".format(self.namespace))

        # Read cache to variable
        self.cache = self.read()

    def read(self):
        """
        Read and return cache file

        @return string
        """
        # Make sure cache exists
        self.create()

        with open(self.location, 'r') as f:
            return json.load(f)

    def create(self):
        """
        Create cache
        """
        if not os.path.exists(self.location):
            # Create cache folder
            if not os.path.exists(os.path.dirname(self.location)):
                os.makedirs(os.path.dirname(self.location))

            # Create cache file
            with open(self.location, 'w') as f:
                f.write(json.dumps({}, indent=4))

    def exists(self, key):
        """
        Check if key exists in entry

        @param string key
        @return boolean
        """
        return self.namespace in self.cache and key in self.cache[self.namespace]

    def get(self, key):
        """
        Get entire entry or specific value for key

        @param string alias
        @param string key (optional)
        @param string default (optional)
        @return string
        """
        if self.namespace in self.cache:
            if key:
                if key in self.cache[self.namespace] and self.cache[self.namespace][key] != "":
                    return self.cache[self.namespace][key]
            else:
                return self.cache[self.namespace]

        return None

    def set(self, key, value):
        """
        Add value to entry

        @param string alias
        @param string key
        @param string value
        """
        if not self.namespace in self.cache:
            self.cache[self.namespace] = {}

        self.cache[self.namespace][key] = value

        self.write()

    def write(self):
        """
        Write cache to file
        """
        with open(self.location, 'w') as f:
            f.write(json.dumps(self.cache, indent=4))
