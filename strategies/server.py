import os
import sys
import subprocess
import re
import datetime

from helpers import util
from helpers import config
from helpers.log import Logger

class Server_Backup:
	name = 'Server'
	type = 'server'

	def __init__(self):
		self.logger = Logger()

	def add(self):
		# Read alias
		alias = input('Alias: ')

		# Check if alias exists
		while config.exists(alias):
			print("This alias already exists")
			alias = input('Alias: ')

		path = input("Path on server: ")
		backup_path = input('Backup path (optional): ') or 'backups/' + alias
		ssh_user = input("SSH user: ")
		ssh_host = input("SSH host: ")
		ssh_pass = input("SSH pass: ")
		versions = input("Keep versions [1]: ") or 1
		archive = input("Archive? [y/N]: ")
		archive = archive != None and archive.lower() == 'y'

		config.set(alias, 'type', self.type)
		config.set(alias, 'path', path)
		config.set(alias, 'backup_path', backup_path)
		config.set(alias, 'ssh_user', ssh_user)
		config.set(alias, 'ssh_host', ssh_host)
		config.set(alias, 'ssh_pass', ssh_pass)
		config.set(alias, 'versions', int(versions))
		config.set(alias, 'archive', archive)
		config.set(alias, 'exclude', [])

		print("Added.")

	def backup(self, alias):
		"""
		Main worker

		@param string alias
		"""
		self.logger.write('### Backup {} ({}) ###'.format(alias, self.name))

		if not config.exists(alias):
			self.logger.write("Alias {} does not exist".format(alias))
			return

		# Read config
		path_from = config.get(alias, 'path')
		backup_path = config.get(alias, 'backup_path')
		ssh_user = config.get(alias, 'ssh_user')
		ssh_host = config.get(alias, 'ssh_host')
		ssh_pass = config.get(alias, 'ssh_pass')
		versions = config.get(alias, 'versions')
		archive = config.get(alias, 'archive')
		exclude = config.get(alias, 'exclude', [])

		# Make sure backup path exists
		util.create_backup_path(backup_path, alias)

		#destination = backup_path if versions < 2 else os.path.join(backup_path, alias + "_" + self.get_timestring())
		#remainder = destination.replace(backup_path, "").strip("/")

		if archive:
			filename = alias if versions < 2 else alias + "_" + self.get_timestring()
			self.archive(ssh_host, ssh_user, ssh_pass, path_from, backup_path, filename, exclude)
		else:
			path_to = backup_path if versions < 2 else os.path.join(backup_path, alias + "_" + self.get_timestring())
			self.sync(ssh_host, ssh_user, ssh_pass, path_from, path_to, exclude)

		# Remove old backups
		util.cleanup_versions(backup_path, versions, alias)

	def sync(self, host, user, password, path_from, path_to, exclude=[]):
		# Escape password
		password = re.escape(password)
		exclude_str = ' '.join(list(map(lambda x: "--exclude '" + x + "'", exclude)))

		# Sync using rsync
		cmd = "sshpass -p {} rsync -a {} -e 'ssh -o StrictHostKeyChecking=no' {}@{}:{} {}/".format(password, exclude_str, user, host, path_from, path_to)
		subprocess.run([cmd], shell=True)

	def archive(self, host, user, password, path_from, path_to, filename, exclude=[]):
		# Get name of folder to be backed up
		basename = os.path.basename(path_from)

		# Escape password
		password = re.escape(password)
		exclude_str = ' '.join(['-x \'' + os.path.join(basename, x) + '*\'' if x.endswith('/') else '-x \'' + os.path.join(basename, x) + '\'' for x in exclude])

		# Create zip on remote server
		cmd = "sshpass -p {} ssh {}@{} -o StrictHostKeyChecking=no \"cd {}/.. && zip -r {}/{}.zip `basename {}` {}\"".format(password, user, host, path_from, path_from, filename, path_from, exclude_str)
		subprocess.run([cmd], shell=True)

		# Pull backups
		cmd = "sshpass -p {} rsync --remove-source-files -a -e ssh {}@{}:{}/{}.zip {}/".format(password, user, host, path_from, filename, path_to)
		subprocess.run([cmd], shell=True)

	def get_timestring(self):
		"""
		Get current timestamp as string

		@return string
		"""
		return datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
