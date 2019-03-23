import os
import datetime
from . import util

class Logger():
    prepared = ""

    def __init__(self):
        project_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        name = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S') + ".log"

        self.prepared = ""
        self.backup_path = os.path.join(project_path, "log", name)

    def prepare(self, msg):
        self.prepared += msg

    def flush(self):
        if self.prepared:
            self.write(self.prepared)
            self.prepared = ""

    ##
    # Write message to log and print to console
    #
    # @param string msg
    def write(self, msg):
        # Create backup folder
        util.create_folder(os.path.dirname(self.backup_path))

        # Build message
        msg = util.get_timestamp(True) + " | " + str(msg)

        # Print message to terminal
        print(msg)

        # Write message to file
        with open(self.backup_path, "a") as logfile:
            logfile.write(msg + "\n")
