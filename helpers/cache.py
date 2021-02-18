"""Cache helper."""

import os

from . import util
from .config import ConfigHelper

class Cache(ConfigHelper):
    """Cache helper."""
    def __init__(self, namespace):
        """
        Constructor

        @param string namespace
        """
        # Determine cache location
        location = os.path.join(util.get_project_path(), 'cache', '{}.json'.format(namespace))

        super().__init__(location=location)
