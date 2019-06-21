import os
import time
import datetime
import hashlib
import smtplib

def create_folder(path):
	"""
	Create folder if not exists

	@param string path Absolute path to folder
	@return string
	"""
	if not os.path.exists(path):
		os.makedirs(path)
		return path

def md5(string):
	"""
	Calculate MD5-Checksum of string

	@param string string
	@return string
	"""
	m = hashlib.md5()
	m.update(string.encode('utf-8'))
	return m.hexdigest()

def md5_file(path):
	"""
	Generate MD5-Hash of a file

	@param string path Path to file
	@return string
	"""
	if not os.path.isfile(path):
		return ""

	hash_md5 = hashlib.md5()
	with open(path, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)
	return hash_md5.hexdigest()

def get_timestamp(format=False):
	"""
	Get current timestamp

	@param boolean format
	@return string|int
	"""
	if format:
		return datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
	else:
		return int(round(time.time() * 1000))

def send_gmail(sender, pwd, recipient, subject, body):
	"""
	Send mail using gmail
	"""
	recipient = recipient if isinstance(recipient, list) else [recipient]

	# Prepare actual message
	message = "From: {}\nTo: {}\nSubject: {}\n\n{}".format(sender, ", ".join(recipient), subject, body)

	try:
		server = smtplib.SMTP("smtp.gmail.com", 587)
		server.ehlo()
		server.starttls()
		server.login(sender, pwd)
		server.sendmail(sender, recipient, message)
		server.close()
	except:
		print("failed to send mail")
