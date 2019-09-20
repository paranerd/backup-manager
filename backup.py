import os
import sys
import argparse
import json

from modules.github import Github_Backup
from modules.googledrive import Google_Drive_Backup
from modules.googlephotos import Google_Photos_Backup
from modules.wordpress import Wordpress_Backup

from modules.log import Logger
from modules import util
from modules import config

modules = [
	{'name': 'GitHub', 'type': 'github', 'module': Github_Backup},
	{'name': 'Google Photos', 'type': 'googlephotos', 'module': Google_Photos_Backup},
	{'name': 'Google Drive', 'type': 'googledrive', 'module': Google_Drive_Backup},
	{'name': 'Wordpress', 'type': 'wordpress', 'module': Wordpress_Backup}
]

def type_to_module(type):
	"""
	Get backup module by type

	@return misc
	"""
	for module in modules:
		if module['type'] == type:
			return module['module']

def prepare():
	"""
	Create config file and cache folder
	"""
	config_location = os.path.join(util.get_project_path(), "config.json")
	cache_location = os.path.join(util.get_project_path(), "cache")

	if not os.path.exists(config_location):
		default_config = {'general': {}}
		with open(config_location, 'w') as config:
			config.write(json.dumps(default_config, indent=4))

	if not os.path.exists(cache_location):
		os.makedirs(cache_location)

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

def show_add_menu():
	"""
	Display menu for adding accounts
	"""
	print('--- Select type: ---')

	for index, entry in enumerate(modules):
		print("[{}] {}".format(index + 1, entry['name']))

	print()
	type = int(input("Type: "))

	try:
		module = modules[type - 1]['module']()
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

	# Prepare environment
	prepare()

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

			if entry:
				module = type_to_module(entry['type'])()
				module.backup(alias)
	else:
		show_help()

	# Mail log
	if config.get('general', 'mail_user') and config.get('general', 'mail_pass'):
		util.send_gmail(config.get('general', 'mail_user'), config.get('general', 'mail_pass'), [config.get('general', 'mail_user')], "Backup My Accounts", "Backup complete.", [Logger.get_path()])

	print("Done root.")
