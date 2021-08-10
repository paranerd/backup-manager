"""Super class for all strategies to provide common basic functionalities."""

import os
import json
import traceback
import logging
import logging.config
import yaml

from helpers import util
from helpers.log_counter_handler import LogCounterHandler
from helpers.config import ConfigHelper


class Strategy:
    """Super class for all strategies to provide common basic functionalities."""
    NAME = None
    TYPE = None
    logger = None
    config = None
    alias = None
    multipart = False
    backup_path = ''
    common_fields = ['backup_path', 'type']

    def __init__(self):
        self.msg_counter_handler = LogCounterHandler()

        self.logger = self.init_logger()

    def init_logger(self, alias=None):
        """Initialize the logger.

        @param string alias (optional)
        """
        alias = alias or self.__class__.__name__

        # Load logger config
        with open(os.path.join('config', 'logger.yaml'), 'r') as f:
            config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)

        logger = logging.getLogger(alias)
        logger.addHandler(self.msg_counter_handler)

        return logger

    def set_logger(self, logger):
        """Explicitly set logger (used for multipart).

        @param Logger logger
        @return self For chaining
        """
        self.logger = logger

        return self

    def get_error_count(self):
        """Get error count from logger handler."""
        if 'ERROR' in self.msg_counter_handler.level_to_count:
            return self.msg_counter_handler.level_to_count['ERROR']
        else:
            return 0

    def get_warning_count(self):
        """Get warnings count from logger handler."""
        if 'WARN' in self.msg_counter_handler.level_to_count:
            return self.msg_counter_handler.level_to_count['WARN']
        else:
            return 0

    def add(self, override={}):
        """Use strategy schema to provice default add prompts.

        @param dict override
        @return string
        """
        alias = override['alias'] if 'alias' in override else input('Alias: ')

        self.config = ConfigHelper()

        if 'alias' not in override:
            # Check if alias exists
            while self.config.exists(alias):
                print('This alias already exists')
                alias = input('Alias: ')

        try:
            # Get config handle
            self.config = ConfigHelper(alias, False)

            # Load schema
            schema = self.load_schema()

            if 'alias' not in override:
                # Set backup path
                backup_path_default = os.path.join(
                    util.get_project_path(), 'backups', alias)
                backup_path = input('Backup path [{}]: '.format(
                    backup_path_default)) or backup_path_default
                self.config.set('backup_path', backup_path)

                # Set type
                the_type = override['type'] if 'type' in override else self.TYPE
                self.config.set('type', the_type)

            # Read parameters
            for param in schema:
                if param['key'] in override:
                    # Use value override
                    self.config.set(param['key'], override[param['key']])
                    continue

                if 'prompt' not in param:
                    # Value is not supposed to be read here
                    continue

                default_str = self.build_default_string(param)
                value = input('{}{}: '.format(param['prompt'], default_str))

                # Try setting default value if no value given
                if value == '' and 'default' in param:
                    value = param['default']

                # Ensure right format
                if 'type' not in param:
                    pass
                elif param['type'] == 'int':
                    value = int(value)
                elif param['type'] == 'bool':
                    value = value.lower() in ['y', 'yes']
                elif param['type'] == 'list':
                    value = value if value else []

                # Write to config
                self.config.set(param['key'], value)

            # Flush config to file
            self.config.write()

            # Enable config write through
            self.config.set_write_through(True)

            return alias
        except KeyboardInterrupt:
            self.logger.info('Aborted')
        except Exception:
            traceback.print_exc()

    def backup(self, alias, multipart=False):
        """Set up proper backup environment.

        @param string alias
        @param boolean multipart (optional)
        @return dict
        """
        try:
            # self.logger.set_source(alias)
            self.logger = self.init_logger(alias)

            if not multipart:
                self.logger.info('Starting...')

            # Get config handle
            self.config = ConfigHelper(alias)

            # Check if config exists
            if not self.config.exists():
                raise Exception('Alias {} does not exist'.format(alias))

            self.alias = alias
            self.multipart = multipart

            # Read config
            self.config = ConfigHelper(alias)

            # Validate config
            self.validate_config()

            # Determine backup path
            if multipart or (self.config.exists('versions') and self.config.get('versions') > 1 and not self.config.get('archive')):
                self.backup_path = os.path.join(self.config.get(
                    'backup_path'), self.alias + '_' + util.startup_time)
            else:
                self.backup_path = self.config.get('backup_path')

            # Make sure backup path exists
            util.create_folder(self.backup_path)

            # Start the actual backup
            self.start_backup()

            # Tear down backup environment
            self.teardown()
        except KeyboardInterrupt:
            self.logger.warn('Interrupted')
        except Exception as err:
            self.logger.error(err)
            traceback.print_exc()

        return {
            'errors': self.get_error_count(),
            'warnings': self.get_warning_count()
        }

    def start_backup(self):
        """Placeholder for method only to be called on child classes."""
        raise NotImplementedError("Must override start_backup")

    def teardown(self):
        """Clean up backup environment."""
        if self.multipart:
            return

        if self.config.get('versions'):
            # Remove old versions
            util.cleanup_versions(self.config.get(
                'backup_path'), self.config.get('versions'), self.alias)

        # Done
        self.logger.info('Done')

    def build_default_string(self, param):
        """Build default value string to be displayed in add prompt.

        @param string param
        @return string
        """
        if 'default' in param:
            if not 'type' in param or param['type'] in ['int']:
                return ' [{}]'.format(param['default'])
            elif param['type'] == 'bool':
                return ' [Y/n]' if param['default'] else ' [y/N]'
        else:
            if 'type' in param and param['type'] == 'bool':
                return ' [y/N]'

        return ''

    def load_schema(self):
        """Load strategy schema.

        @return list
        """
        # Determine config location
        location = os.path.join(util.get_project_path(),
                                'config', 'schemas', self.TYPE + '.json')

        if not os.path.exists(location):
            return []

        with open(location, 'r') as f:
            return json.load(f)

    def validate_config(self):
        """Check config for missing required values.

        @raises Exception
        """
        # Load schema
        schema = self.load_schema()

        # Determine all required fields
        required_fields = self.common_fields +\
            list(map(lambda x: x['key'], filter(
                lambda x: 'required' not in x or x['required'], schema)))

        # Check if we have all necessary information
        for field in required_fields:
            if self.config.get(field, '') == '':
                raise Exception(
                    'Config corrupted: "{}" is missing'.format(field))
