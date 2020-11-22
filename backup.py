import os
import sys
import argparse
import json

from strategies.github import Github
from strategies.googledrive import GoogleDrive
from strategies.googlephotos import GooglePhotos
from strategies.wordpress import Wordpress
from strategies.dropbox import Dropbox
from strategies.mysql import MySQL
from strategies.server import Server
from strategies.mongodb import MongoDB

from helpers import util
from helpers.log import Logger
from helpers import config

modules = [
    Github,
    GooglePhotos,
    GoogleDrive,
    Wordpress,
    Dropbox,
    MySQL,
    Server,
    MongoDB
]

def type_to_module(type):
    """
    Get backup module by type

    @return misc
    """
    for module in modules:
        if module.TYPE == type:
            return module

def parse_args():
    """
    Parse command line arguments

    @return dict
    """
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--add', action='store_true')
    parser.add_argument('--backup', action='store_true')
    args, leftovers = parser.parse_known_args()

    return args

def configure_mail():
    """
    Add main credentials to config
    """
    mail_user = input('Mail username [None]: ')

    if mail_user:
        mail_pass = input('Mail password: ')
    else:
        mail_pass = ""

    config.set('general', 'mail_user', mail_user)
    config.set('general', 'mail_pass', mail_pass)

def format_mail_body(warnings, errors):
    """
    Format mail body

    @param int warnings
    @param int errors

    @return string
    """
    return "<h1>Backup My Accounts</h1><p>Backup complete</p><p>{} Warnings</p><p>{} Errors</p>".format(warnings, errors)

def show_add_menu():
    """
    Display menu for adding accounts
    """
    print('--- Select type: ---')

    for index, entry in enumerate(modules):
        print("[{}] {}".format(index + 1, entry.NAME))

    print()
    type = int(input("Type: "))

    try:
        module = modules[type - 1]()
        module.add()
    except Exception as e:
        print(e)

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

if __name__ == "__main__":
    args = parse_args()

    # Count warnings and errors
    warnings = 0
    errors = 0

    # Configure mail if necessary
    if not config.exists('general', 'mail_user'):
        configure_mail()

    # If add
    if args.add:
        show_add_menu()
    elif args.backup:
        aliases = sys.argv[2:] if len(sys.argv) > 2 else list(config.config.keys())

        for alias in aliases:
            entry = config.get(alias)

            if entry and alias != "general":
                module = type_to_module(entry['type'])()
                res = module.backup(alias)

                warnings += res['warnings']
                errors += res['errors']
    else:
        show_help()
        sys.exit(1)

    # Mail log
    mail_body = format_mail_body(warnings, errors)

    if config.get('general', 'mail_user') and config.get('general', 'mail_pass'):
        util.send_gmail(config.get('general', 'mail_user'), config.get('general', 'mail_pass'), [config.get('general', 'mail_user')], "Backup My Accounts", mail_body, [Logger.get_path()])
