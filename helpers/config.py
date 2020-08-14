import os
import json

from . import util

# Determine config location
location = os.path.join(util.get_project_path(), "config", "config.json")

def read():
	"""
	Read and return config file

	@return string
	"""
	# Make sure config exists
	create()

	with open(location, 'r') as f:
		return json.load(f)

def create():
	"""
	Create config
	"""
	if not os.path.exists(location):
		with open(location, 'w') as f:
			f.write(json.dumps({'general': {}}, indent=4))

def exists(alias, key=None):
	"""
	Check if key exists in entry

	@param string alias
	@param string key (optional)
	@return boolean
	"""
	return alias in config and (key == None or key in config[alias])

def get(alias, key=None, default=""):
	"""
	Get entire entry or specific value for key

	@param string alias
	@param string key (optional)
	@param string default (optional)
	@return string
	"""
	if alias in config:
		if key:
			if key in config[alias] and config[alias][key] != "":
				return config[alias][key]
		else:
			return config[alias]

	return default

def set(alias, key, value):
	"""
	Add value to entry

	@param string alias
	@param string key
	@param string value
	"""
	if not alias in config:
		config[alias] = {}

	config[alias][key] = value
	write()

def write():
	"""
	Write config to file
	"""
	with open(location, 'w') as f:
		f.write(json.dumps(config, indent=4))

# Read config to variable
config = read()
