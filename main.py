"""Entry point for backup."""

import os
import sys
import argparse
import shutil

from strategies.github import Github
from strategies.gist import Gist
from strategies.googledrive import GoogleDrive
from strategies.googlephotos import GooglePhotos
from strategies.wordpress import Wordpress
from strategies.dropbox import Dropbox
from strategies.mysql import MySQL
from strategies.server import Server
from strategies.mongodb import MongoDB
from strategies.postgresql import PostgreSQL

from helpers import util
from helpers import mail
from helpers.log import Logger
from helpers.config import ConfigHelper

strategies = [
    Github,
    Gist,
    GooglePhotos,
    GoogleDrive,
    Wordpress,
    Dropbox,
    MySQL,
    Server,
    MongoDB,
    PostgreSQL
]

config = ConfigHelper('')

def type_to_strategy(strategy_type):
    """
    Get backup module by type.

    @param string type
    @return misc
    """
    for strategy in strategies:
        if strategy.TYPE == strategy_type:
            return strategy

    return None

def parse_args():
    """
    Parse command line arguments.

    @return dict
    """
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--add', action='store_true')
    parser.add_argument('--backup', action='store_true')
    arguments, _ = parser.parse_known_args()

    return arguments

def configure_mail():
    """
    Add mail credentials to config.
    """
    mail_user = input('Mail username [None]: ')

    if mail_user:
        mail_pass = input('Mail password: ')
    else:
        mail_pass = ''

    config.set('general.mail_user', mail_user)
    config.set('general.mail_pass', mail_pass)

def format_mail_body(warnings, errors):
    """
    Format mail body.

    @param int warnings
    @param int errors

    @return string
    """
    body = '<h1>Backup complete</h1>'
    body += '<p>{} Warning(s)</p>'.format(warnings)
    body += '<p>{} Error(s)</p>'.format(errors)

    return body

def show_add_menu():
    """
    Display menu for adding accounts
    """
    print('--- Select type: ---')

    for index, entry in enumerate(strategies):
        print('[{}] {}'.format(index + 1, entry.NAME))

    print()
    backup_type = None

    while not backup_type or not backup_type.isnumeric() or\
        not 0 < int(backup_type) <= len(strategies):
        backup_type = input('Type: ')

    backup_type = int(backup_type)

    try:
        strategy = strategies[backup_type - 1]()
        strategy.add()
    except Exception as err:
        print(err)

def show_help():
    """
    Show help
    """
    print('--- Usage ---')
    print('\tpython3 backup.py [--add] [--backup [alias1, alias2]]')
    print()
    print('Arguments:')
    print('\t--add: Add a new account to backup')
    print('\t--backup: Start the backup (optionally followed by aliases to be backed up exclusively)')

if __name__ == '__main__':
    args = parse_args()

    # Initialize Logger
    logger = Logger('main')

    # Count warnings and errors
    warnings = 0
    errors = 0

    # Configure mail if necessary
    if not config.exists('general.mail_user'):
        configure_mail()

    # If add
    if args.add:
        show_add_menu()
    elif args.backup:
        aliases = sys.argv[2:] if len(sys.argv) > 2 else list(config.config.keys())

        for alias in aliases:
            entry = config.get(alias)

            if not entry:
                logger.error('Entry "{}" not found'.format(alias))
                sys.exit(1)

            if alias != 'general':
                module = type_to_strategy(entry['type'])()
                res = module.backup(alias)

                warnings += int(res['warnings'])
                errors += int(res['errors'])
    else:
        show_help()
        sys.exit(1)

    # Clean up
    tmp_path = util.get_tmp_path()

    if os.path.isdir(tmp_path):
        shutil.rmtree(tmp_path)

    # Mail log
    if config.get('general.mail_user') and config.get('general.mail_pass') and os.path.exists(Logger.get_path()):
        mail_body = format_mail_body(warnings, errors)
        mail.send_gmail(config.get('general.mail_user'), config.get('general.mail_pass'), [config.get('general.mail_user')], 'Backup My Accounts', mail_body, [Logger.get_path()])
