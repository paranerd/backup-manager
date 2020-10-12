import os
import datetime
from . import util

# Get project path
project_path = util.get_project_path()

# Path to logs folder
logs_path = os.path.join(project_path, "log")

# Set current log path
name = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
path = os.path.join(project_path, "log", name) + ".txt"

class Logger():
	buffer = ""

	def __init__(self):
		"""
		Constructor
		"""
		# Create logs folder
		util.create_folder(logs_path)

	def addToBuffer(self, msg):
		"""
		Buffer log message without immediate writing

		@param string msg Log message
		"""
		self.buffer += msg

	def flush(self):
		"""
		Write buffered log message
		"""
		if self.buffer:
			self.write(self.buffer)
			self.buffer = ""

	@staticmethod
	def get_path():
		"""
		Get current log path

		@return string
		"""
		return path

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
		with open(path, "a") as logfile:
			logfile.write(msg + "\n")

	def get(self):
		"""
		Get current log

		@return string
		"""
		with open(path, "r") as file:
			return file.read()
