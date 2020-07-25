import os
import sys
import subprocess
import re
import datetime

from .mysql import MySQL_Backup
from .server import Server_Backup

from helpers import util
from helpers import config
from helpers.log import Logger

class Wordpress_Backup:
	name = "WordPress"
	type = "wordpress"

	def __init__(self):
		self.timestamp = self.get_timestring()
		self.logger = Logger()

	def add(self):
		# Read alias
		alias = input('Alias: ')

		# Check if alias exists
		while config.exists(alias):
			print("This alias already exists")
			alias = input('Alias: ')

		webroot = input("Webroot: ")
		backup_path = input('Backup path (optional): ') or 'backups/' + alias
		versions = input("Keep versions [1]: ") or 1
		ssh_user = input("SSH user: ")
		ssh_host = input("SSH host: ")
		ssh_pass = input("SSH pass: ")
		db_name = input("Database name: ")
		db_user = input("Database user: ")
		db_host = input("Database host [{}]: ".format(ssh_host)) or ssh_host
		db_pass = input("Database password: ")

		config.set(alias, 'type', 'wordpress')
		config.set(alias, 'webroot', webroot)
		config.set(alias, 'backup_path', backup_path)
		config.set(alias, 'versions', int(versions))
		config.set(alias, 'ssh_user', ssh_user)
		config.set(alias, 'ssh_host', ssh_host)
		config.set(alias, 'ssh_pass', ssh_pass)
		config.set(alias, 'db_name', db_name)
		config.set(alias, 'db_user', db_user)
		config.set(alias, 'db_host', db_host)
		config.set(alias, 'db_pass', db_pass)

		print("Added.")

	def get_timestring(self):
		"""
		Get current timestamp as string

		@return string
		"""
		return datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')

	def escape_string(self, string):
		"""
		Escape string to be used in bash

		@param string string
		@return string
		"""
		return re.escape(string)

	def backup(self, alias):
		"""
		Main worker

		@param string alias
		"""
		self.logger.write('### Backup {} (WordPress) ###'.format(alias))

		if not config.exists(alias):
			self.logger.write("Alias {} does not exist".format(alias))
			return

		# Read config
		webroot = config.get(alias, 'webroot')
		backup_path = config.get(alias, 'backup_path')
		versions = config.get(alias, 'versions')
		ssh_user = config.get(alias, 'ssh_user')
		ssh_host = config.get(alias, 'ssh_host')
		ssh_pass = config.get(alias, 'ssh_pass')
		db_name = config.get(alias, 'db_name')
		db_user = config.get(alias, 'db_user')
		db_host = config.get(alias, 'db_host')
		db_pass = config.get(alias, 'db_pass')

		# Make sure backup path exists
		util.create_backup_path(backup_path, alias)

		# Check if we have all necessary information
		if not webroot or not backup_path or not ssh_user or not ssh_host \
			or not ssh_pass or not db_name or not db_user or not db_host or not db_pass:
			raise Exception("Config corrupted")

		# Determine version name
		version_name = self.get_timestring()

		# Create backup folder
		path_to = util.create_folder(os.path.join(backup_path, alias + "_" + version_name))

		# Backup database
		db = MySQL_Backup()
		db.download(db_name, db_host, db_user, db_pass, path_to, version_name)

		# Backup files
		server = Server_Backup()
		server.archive(ssh_host, ssh_user, ssh_pass, webroot, path_to, version_name)

		# Remove old versions
		util.cleanup_versions(backup_path, versions, alias)

		# Add list of backed up files to log
		self.log_filelist(backup_path, alias)

	def log_filelist(self, backup_path, alias):
		"""
		Add files in backup to log

		@param string backup_path
		"""
		for file in os.listdir(backup_path):
			if file.startswith(alias):
				self.logger.write(file)
