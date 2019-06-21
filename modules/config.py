import os
import json

location = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "config.json")

def read():
	with open(location, 'r') as f:
		return json.load(f)

def exists(module, key):
	return module in config and key in config[module]

def get(module, key, default=""):
	return config[module][key] if module in config and key in config[module] and config[module][key] != "" else default

def set(module, key, value):
	if not module in config:
		config[module] = {}
		write()

	config[module][key] = value
	write()

def write():
	with open(location, 'w') as f:
		f.write(json.dumps(config, indent=4))

config = read()
