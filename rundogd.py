#!/usr/bin/env python

# Copyright 2011 Jason Oster. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   1. Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY JASON OSTER ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL JASON OSTER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of Jason Oster.

import os
import subprocess
import sys
import time

from argparse import ArgumentParser
from threading import Timer

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

version = "0.1"


def run(command, process=None):
    if process:
        process.terminate()

    print "$", " ".join(command)
    try:
        return subprocess.Popen(command)
    except OSError as e:
        print "Failed to start process:", e
        sys.exit(1)


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, command, process, **kwargs):
        self.command = command
        self.process = process
        self.timer = None

        FileSystemEventHandler.__init__(self, **kwargs)

    def on_any_event(self, event):
        def restart():
            print "---------- Restarting... ----------"
            self.process = run(self.command, self.process)

        ## Restart after 100ms has passed
        # This ensures all file events have completed
        # by the time the command is restarted.
        if ((not self.timer) or
            (not self.timer.is_alive())):
            self.timer = Timer(0.1, restart)
            self.timer.start()


if __name__ == "__main__":
    # Parse command line arguments
    parser = ArgumentParser(
        description="Filesystem watcher-restarter daemon.",
        usage="%(prog)s [options] command",
        prog="rundogd"
    )
    parser.add_argument(
        "-p", "--path",
        action="append",
        nargs=1,
        help="recursively watch for file changes in this path"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s " + version
    )
    args = parser.parse_known_args()

    # Require a command
    if len(args[1]) == 0:
        parser.error("Missing command.")

    # Get path arguments
    if args[0].path:
        paths = map(lambda x: x[0], args[0].path)
    else:
        # Or infer it from the command
        paths = [ os.path.expanduser(os.path.dirname(args[1][0])) ]

    ## Validate path arguments
    # Replace empty path with current working directory
    for i, path in enumerate(paths):
        if not path:
            paths[i] = "."

    # Remove duplicate paths
    paths = set(paths)

    # Ensure all paths are directories
    for path in paths:
        if not os.path.isdir(path):
            print path, "is not a directory."
            sys.exit(1)

    # Get command argument, and start the process
    command = args[1]
    process = run(command)

    # Start the watchdog observer thread
    event_handler = ChangeHandler(command, process)
    observer = Observer()
    for path in paths:
        observer.schedule(event_handler, path=path, recursive=True)
    observer.start()

    # Enter Rip Van Winkle mode
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass

    print "\nrundogd is shutting down..."
    observer.stop()
    observer.join()
