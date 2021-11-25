"""Override of the default argparse behaviour for argument errors."""

import argparse
import sys

class ArgumentParser(argparse.ArgumentParser):
  def __init__(self):
    argparse.ArgumentParser.__init__(self, allow_abbrev=False)

  def error(self, message):
    self.print_help(sys.stderr)
    sys.exit(2)
