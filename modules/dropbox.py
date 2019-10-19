import os
import dropbox

from . import util
from . import config
from . import cache
from .log import Logger

class Dropbox_Backup:
	alias = ''

	def __init__(self):
		self.logger = Logger()

	def add(self):
		"""
		Add Dropbox account
		"""
		# Read alias
		alias = input('Alias: ')

		# Check if alias exists
		while config.exists(alias):
			print("This alias already exists")
			alias = input('Alias: ')

		# Read access token
		token = input('Access token: ')

		# Read backup path
		backup_path = input('Backup path (optional): ')
		backup_path = backup_path if backup_path else 'backups/' + alias

		# Write config
		config.set(alias, 'type', 'dropbox')
		config.set(alias, 'token', token)
		config.set(alias, 'backup_path', backup_path)

		print("Added.")

	def backup(self, alias):
		"""
		Main worker

		@param string alias
		"""
		self.logger.write("")
		self.logger.write("### Backup {} (Dropbox) ###".format(alias))
		self.logger.write("")

		try:
			self.alias = alias
			token = config.get(alias, 'token')
			self.dbx = dropbox.Dropbox(token)
			self.backup_path = config.get(alias, 'backup_path')
			util.create_backup_path(self.backup_path, alias)
			self.exclude = config.get(alias, 'exclude', [])

			if not token:
				raise Exception("Token not set")

			# Get files recursively
			self.get_children()

			# Done
			self.logger.write("Finished Dropbox backup")

		except Exception as e:
			self.logger.flush()
			self.logger.write(e)

	def get_children(self, path=""):
		res = self.dbx.files_list_folder(path=path)

		for entry in res.entries:
			if self.check_if_excluded(entry.path_display):
				continue
			elif isinstance(entry, dropbox.files.FolderMetadata):
				self.get_children(entry.path_display)
			else:
				destination = os.path.join(self.backup_path, entry.path_display.strip('/'))
				self.logger.write(entry.path_display)

				hash = cache.get(self.alias, entry.path_display)

				if not os.path.isfile(destination) or hash != entry.content_hash:
					cache.set(self.alias, entry.path_display, entry.content_hash)
					self.download(entry.path_display, destination)

	def download(self, dropbox_path, destination):
		parent = os.path.dirname(destination)

		if not os.path.exists(parent):
			os.makedirs(parent)

		with open(destination, "wb+") as f:
			metadata, res = self.dbx.files_download(path=dropbox_path)
			f.write(res.content)

	def check_if_excluded(self, path):
		for e in self.exclude:
			if re.match(e, path):
				return True

		return False
