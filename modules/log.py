import os
import datetime
from . import util

class Logger():
	prepared = ""
	project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
	logs_path = os.path.join(project_path, "log")
	lock_path = os.path.join(logs_path, "lock")

	def __init__(self):
		"""
		Constructor
		"""
		# Create logs folder
		util.create_folder(self.logs_path)

		# Set current log path
		self.path = self.set_path()

	def prepare(self, msg):
		"""
		Prepare log message without immediate writing

		@param string msg Log message
		"""
		self.prepared += msg

	def flush(self):
		"""
		Write prepared log message
		"""
		if self.prepared:
			self.write(self.prepared)
			self.prepared = ""

	def set_path(self):
		"""
		Set current log path

		@return string
		"""
		name = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
		return os.path.join(self.project_path, "log", name) + ".txt"

	def get_path(self):
		"""
		Get current log path

		@return string
		"""
		return self.path

	def write(self, msg):
		"""
		Write message to log and print to console

		@param string msg Log message
		"""
		# Build message
		msg = util.get_timestamp(True) + " | " + str(msg)

		# Print message to terminal
		print(msg)

		# Write message to file
		with open(self.path, "a") as logfile:
			logfile.write(msg + "\n")

	def get(self):
		"""
		Get current log

		@return string
		"""
		with open(self.path, "r") as file:
			return file.read()
