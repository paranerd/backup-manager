import os
import json

from . import util

# Determine cache location
location = os.path.join(util.get_project_path(), "cache", "cache.json")

def read():
	"""
	Read and return cache file

	@return string
	"""
	# Make sure cache exists
	create()

	with open(location, 'r') as f:
		return json.load(f)

def create():
	"""
	Create cache
	"""
	if not os.path.exists(location):
		# Create cache folder
		if not os.path.exists(os.path.dirname(location)):
			os.makedirs(os.path.dirname(location))

		# Create cache file
		with open(location, 'w') as f:
			f.write(json.dumps({}, indent=4))

def exists(alias, key=None):
	"""
	Check if key exists in entry

	@param string alias
	@param string key (optional)
	@return boolean
	"""
	return alias in cache and (key == None or key in cache[alias])

def get(alias, key=None, default=""):
	"""
	Get entire entry or specific value for key

	@param string alias
	@param string key (optional)
	@param string default (optional)
	@return string
	"""
	if alias in cache:
		if key:
			if key in cache[alias] and cache[alias][key] != "":
				return cache[alias][key]
		else:
			return cache[alias]

	return default

def set(alias, key, value):
	"""
	Add value to entry

	@param string alias
	@param string key
	@param string value
	"""
	if not alias in cache:
		cache[alias] = {}
		write()

	cache[alias][key] = value
	write()

def write():
	"""
	Write cache to file
	"""
	with open(location, 'w') as f:
		f.write(json.dumps(cache, indent=4))

# Read cache to variable
cache = read()
