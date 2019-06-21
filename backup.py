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

config_location = os.path.join(os.path.dirname(__file__), "config.json")
cache_location = os.path.join(os.path.dirname(__file__), "cache")

def prepare():
	if not os.path.exists(config_location):
		default_config = {'general': {}}
		with open(config_location, 'w') as config:
			config.write(json.dumps(default_config, indent=4))

	if not os.path.exists(cache_location):
		os.makedirs(cache_location)

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--github', action='store_true')
	parser.add_argument('--googledrive', action='store_true')
	parser.add_argument('--googlephotos', action='store_true')
	parser.add_argument('--wordpress', action='store_true')

	return parser.parse_args()

def configure_mail():
	mail_user = input('Mail username [None]: ')

	if mail_user:
		mail_pass = input('Mail password: ')
	else:
		mail_pass = ""

	config.set('general', 'mail_user', mail_user)
	config.set('general', 'mail_pass', mail_pass)

if __name__ == "__main__":
	# Prepare environment
	prepare()

	# Configure mail if necessary
	if not config.exists('general', 'mail_user'):
		configure_mail()

	# Get logger instance so every module writes to the same lock
	logger = Logger()

	# Get arguments
	args = parse_args()

	if not len(sys.argv) > 1:
		sys.exit("No arguments")

	# Start backups
	if args.github:
		git = Github_Backup(logger)
		git.backup()
	if args.googledrive:
		gd = Google_Drive_Backup(logger)
		gd.backup()
	if args.googlephotos:
		gp = Google_Photos_Backup(logger)
		gp.backup()
	if args.wordpress:
		wp = Wordpress_Backup(logger)
		wp.backup()

	if config.get('general', 'mail_user') and config.get('general', 'mail_pass'):
		util.send_gmail(config.get('general', 'mail_user'), config.get('general', 'mail_pass'), config.get('general', 'mail_user'), "Backup Log", logger.get())
