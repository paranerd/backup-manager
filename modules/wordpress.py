import subprocess
import re
import datetime

from . import util
from . import config

class Wordpress_Backup:
	module = 'wordpress'

	def __init__(self, logger):
		self.timestamp = self.get_timestring()
		self.logger = logger

		self.webroot = config.get(self.module, 'webroot')
		self.backup_path = config.get(self.module, 'backup_path')
		self.ssh_user = config.get(self.module, 'ssh_user')
		self.ssh_host = config.get(self.module, 'ssh_host')
		self.ssh_pass = config.get(self.module, 'ssh_pass')
		self.db_name = config.get(self.module, 'db_name')
		self.db_user = config.get(self.module, 'db_user')
		self.db_host = config.get(self.module, 'db_host')
		self.db_pass = config.get(self.module, 'db_pass')

		if not self.webroot:
			self.webroot = input("Webroot: ")
			config.set(self.module, 'webroot', self.webroot)
		if not self.backup_path:
			self.backup_path = input("Backup path: ")
			config.set(self.module, 'backup_path', self.backup_path)
		if not self.ssh_user:
			self.ssh_user = input("SSH user: ")
			config.set(self.module, 'ssh_user', self.ssh_user)
		if not self.ssh_host:
			self.ssh_host = input("SSH host: ")
			config.set(self.module, 'ssh_host', self.ssh_host)
		if not self.ssh_pass:
			self.ssh_pass = input("SSH pass: ")
			config.set(self.module, 'ssh_pass', self.ssh_pass)
		if not self.db_name:
			self.db_name = input("Database name: ")
			config.set(self.module, 'db_name', self.db_name)
		if not self.db_user:
			self.db_user = input("Database user: ")
			config.set(self.module, 'db_user', self.db_user)
		if not self.db_host:
			self.db_host = input("Database host: ")
			config.set(self.module, 'db_host', self.db_host)
		if not self.db_pass:
			self.db_pass = input("Database password: ")
			config.set(self.module, 'db_pass', self.db_pass)

		self.ssh_pass = self.escape_string(self.ssh_pass)
		self.db_pass = self.escape_string(self.db_pass)

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

	def backup(self):
		"""
		Main worker
		"""
		self.logger.write('### Backup WordPress ###')

		# Backup the database into that folder
		cmd = "sshpass -p {} ssh {}@{} -o StrictHostKeyChecking=no \"mkdir -p backups/{} && mysqldump {} --add-drop-table -h {} -u {} -p{} > backups/{}/{}_database.sql\"".format(self.ssh_pass, self.ssh_user, self.ssh_host, self.timestamp, self.db_name, self.db_host, self.db_user, self.db_pass, self.timestamp, self.timestamp)
		subprocess.run([cmd], shell=True)

		# Backup all the files into that folder (excluding the backups)
		cmd = "sshpass -p {} ssh {}@{} -o StrictHostKeyChecking=no \"mkdir -p backups/{} && zip -r backups/{}/{}_files.zip {} -x {}/backups/\*\"".format(self.ssh_pass, self.ssh_user, self.ssh_host, self.timestamp, self.timestamp, self.timestamp, self.webroot, self.webroot)
		subprocess.run([cmd], shell=True)

		# Remove all but the last 5 backups
		cmd = "sshpass -p {} ssh {}@{} -o StrictHostKeyChecking=no \"ls -tp -d -1 {}/backups/** | tail -n +5 | xargs -d '\\n' -r rm -r --\"".format(self.ssh_pass, self.ssh_user, self.ssh_host, self.webroot)
		subprocess.run([cmd], shell=True)

		# Pull backups
		cmd = "sshpass -p {} rsync -a -e ssh {}@{}:{}/backups/ {}".format(self.ssh_pass, self.ssh_user, self.ssh_host, self.webroot, self.backup_path)
		subprocess.run([cmd], shell=True)

		# Add list of backed up files to log
		self.log_filelist()

	def log_filelist(self):
		"""
		Add files in backup to log
		"""
		for file in os.listdir(self.backup_path):
			self.logger.write(file)
