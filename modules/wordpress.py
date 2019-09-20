import os
import sys
import subprocess
import re
import datetime

from . import util
from . import config
from .log import Logger

class Wordpress_Backup:
	keep_backups = 2

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
		backup_path = input('Backup path (optional): ')
		backup_path = backup_path if backup_path else 'backups/' + alias
		ssh_user = input("SSH user: ")
		ssh_host = input("SSH host: ")
		ssh_pass = input("SSH pass: ")
		db_name = input("Database name: ")
		db_user = input("Database user: ")
		db_host = input("Database host: ")
		db_pass = input("Database password: ")

		config.set(alias, 'type', 'wordpress')
		config.set(alias, 'webroot', webroot)
		config.set(alias, 'backup_path', backup_path)
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

		# Read config
		webroot = config.get(alias, 'webroot')
		backup_path = config.get(alias, 'backup_path')
		ssh_user = config.get(alias, 'ssh_user')
		ssh_host = config.get(alias, 'ssh_host')
		ssh_pass = config.get(alias, 'ssh_pass')
		db_name = config.get(alias, 'db_name')
		db_user = config.get(alias, 'db_user')
		db_host = config.get(alias, 'db_host')
		db_pass = config.get(alias, 'db_pass')

		# Check if we have all necessary information
		if not webroot or not backup_path or not ssh_user or not ssh_host \
			or not ssh_pass or not db_name or not db_user or not db_host or not db_pass:
			raise Exception("Config corrupted")

		# Sanitize passwords
		ssh_pass = self.escape_string(ssh_pass)
		db_pass = self.escape_string(db_pass)

		# Create backup folder
		destination = util.create_folder(os.path.join(backup_path, self.timestamp))

		# Dump MySQL
		cmd = "mysqldump {} --add-drop-table -h {} -u {} -p{} > {}/{}.sql".format(db_name, db_host, db_user, db_pass, destination, self.timestamp)
		subprocess.run([cmd], shell=True)

		cmd = "sshpass -p {} ssh {}@{} -o StrictHostKeyChecking=no \"zip -r {}/{}.zip {}\"".format(ssh_pass, ssh_user, ssh_host, webroot, self.timestamp, webroot)
		subprocess.run([cmd], shell=True)

		# Pull backups
		cmd = "sshpass -p {} rsync --remove-source-files -a -e ssh {}@{}:{}/{}.zip {}/".format(ssh_pass, ssh_user, ssh_host, webroot, self.timestamp, destination)
		subprocess.run([cmd], shell=True)

		# Remove old backups
		self.remove_old_backups(backup_path)

		# Add list of backed up files to log
		self.log_filelist(backup_path)

	def remove_old_backups(self, backup_path):
		"""
		Remove all but the latest x backups
		"""
		folders = os.listdir(backup_path)
		folders = [os.path.join(backup_path, f) for f in folders]
		folders.sort(key=lambda x: os.path.getmtime(x), reverse=True)

		for folder in folders[self.keep_backups:]:
			util.remove_folder(folder)

	def log_filelist(self, backup_path):
		"""
		Add files in backup to log

		@param string backup_path
		"""
		for file in os.listdir(backup_path):
			self.logger.write(file)
