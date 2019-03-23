import os
import datetime
from . import util

class Logger():
    prepared = ""
    project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    logs_path = os.path.join(project_path, "log")
    lock_path = os.path.join(logs_path, "lock")

    def __init__(self):
        # Create logs folder
        util.create_folder(self.logs_path)

        # Set current log path
        self.path = self.set_path()

    ##
    # Prepare log message without immediate writing
    #
    # @param string msg Log message
    def prepare(self, msg):
        self.prepared += msg

    ##
    # Write prepared log message
    #
    def flush(self):
        if self.prepared:
            self.write(self.prepared)
            self.prepared = ""

    ##
    # Set current log path
    #
    def set_path(self):
        name = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
        return os.path.join(self.project_path, "log", name)

    ##
    # Write message to log and print to console
    #
    # @param string msg Log message
    def write(self, msg):
        # Build message
        msg = util.get_timestamp(True) + " | " + str(msg)

        # Print message to terminal
        print(msg)

        # Write message to file
        with open(self.path, "a") as logfile:
            logfile.write(msg + "\n")
