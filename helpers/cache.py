"""Cache helper."""

from pathlib import Path

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
        location = Path(util.get_project_path()).joinpath(
            'cache', '{}.json'.format(namespace))

        super().__init__(location=location)
