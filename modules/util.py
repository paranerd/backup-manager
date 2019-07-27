import os
import time
import datetime
import hashlib
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

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

def send_gmail(send_from, pwd, send_to, subject, text, files=None):
	"""
	Send E-Mail using GMail

	@param send_from string
	@param pwd       string
	@param send_to   list
	@param subject   string
	@param text      string
	@param files     list
	"""
	msg = MIMEMultipart()
	msg['From'] = send_from
	msg['To'] = COMMASPACE.join(send_to)
	msg['Date'] = formatdate(localtime=True)
	msg['Subject'] = subject

	msg.attach(MIMEText(text))

	for f in files or []:
		with open(f, "rb") as fil:
			part = MIMEApplication(fil.read(), Name=os.path.basename(f))

		# After the file is closed
		part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
		msg.attach(part)

	try:
		smtp = smtplib.SMTP("smtp.gmail.com", 587)
		smtp.ehlo()
		smtp.starttls()
		smtp.login(send_from, pwd)
		smtp.sendmail(send_from, send_to, msg.as_string())
		smtp.close()
	except:
		print("Failed to send mail")
