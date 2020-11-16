import os
import datetime
from . import util

# Get project path
project_path = util.get_project_path()

# Path to logs folder
logs_path = os.path.join(project_path, "log")

# Set current log path
name = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
path = os.path.join(project_path, "log", name) + ".log"

class Logger():
    buffer = ""
    source = ""
    log_levels = {
        "DEBUG": "DEBUG",
        "INFO": "INFO",
        "WARN": "WARN",
        "ERROR": "ERROR"
    }
    counts = {
        "DEBUG": 0,
        "INFO": 0,
        "WARN": 0,
        "ERROR": 0
    }

    def __init__(self, source=""):
        """
        Constructor

        @param string source
        """
        # Set source
        self.source = source

        # Create logs folder
        util.create_folder(logs_path)

    @staticmethod
    def get_path():
        """
        Gets current log path

        @return string
        """
        return path
    
    def set_source(self, source):
        """
        Sets log source

        @param string source
        """
        self.source = source

    def addToBuffer(self, msg):
        """
        Buffer log message without immediate writing

        @param string msg Log message
        """
        self.buffer += msg

    def debug(self, msg=""):
        """
        Adds debug message

        @param string msg
        """
        self.counts['DEBUG'] += 1
        self._write(msg, self.log_levels['DEBUG'])

    def info(self, msg=""):
        """
        Adds info message

        @param string msg
        """
        self.counts['INFO'] += 1
        self._write(msg, self.log_levels['INFO'])

    def warn(self, msg=""):
        """
        Adds warn message

        @param string msg
        """
        self.counts['WARN'] += 1
        self._write(msg, self.log_levels['WARN'])

    def error(self, msg=""):
        """
        Adds error message

        @param string msg
        """
        self.counts['ERROR'] += 1
        self._write(msg, self.log_levels['ERROR'])

    def _write(self, msg, level):
        """
        Writes message to log and print to console

        @param string msg Log message
        @param string level Log level
        """
        # Prepend buffer if any
        if self.buffer:
            msg = self.buffer + msg

        timestamp = datetime.datetime.now().astimezone().isoformat()

        # Format message
        msg = timestamp + " | " + level + " | " + self.source + " | " + str(msg)

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

    def count_warnings(self):
        """
        Get number of warnings

        @return int
        """
        return self.counts['WARN']

    def count_errors(self):
        """
        Get number of errors

        @return int
        """
        return self.counts['ERROR']