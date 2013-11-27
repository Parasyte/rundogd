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

import argparse
import os
import subprocess
import sys
import time

from threading import Timer

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

version = "0.1"


class Runner():
    def __init__(self, command, stdout=None, stderr=None):
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.outfp = None
        self.errfp = None
        self.process = None
        self.restart()

    def poll(self):
        if self.process:
            try:
                self.process.poll()
                return self.process.returncode
            except OSError:
                self.process = None
        return None

    def terminate(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait()
            except OSError:
                pass
            self.process = None

    def restart(self):
        self.terminate()

        if self.outfp:
            os.close(self.outfp)
        if self.errfp:
            os.close(self.errfp)

        print "$", " ".join(self.command)
        try:
            if self.stdout:
                self.outfp = os.open(
                    self.stdout,
                    os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                    0644
                )
            if self.stderr:
                self.errfp = os.open(
                    self.stderr,
                    os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                    0644
                )

            self.process = subprocess.Popen(
                self.command,
                stdout=self.outfp,
                stderr=self.errfp
            )
        except OSError as e:
            print "Failed to start process:", e
            sys.exit(1)


class ChangeHandler(PatternMatchingEventHandler):
    def __init__(self, runner, wait, verbosity, **kwargs):
        self.runner = runner
        self.wait = wait
        self.verbosity = verbosity
        self.timer = None

        PatternMatchingEventHandler.__init__(self, **kwargs)

    def on_any_event(self, event):
        if self.verbosity:
            if hasattr(event, 'src_path'):
                print '[RUNDOGDEBUG] event src_path:', event.src_path
            if hasattr(event, 'dest_path'):
                print '[RUNDOGDEBUG] event dest_path:', event.dest_path

        def restart():
            print "---------- Restarting... ----------"
            self.runner.restart()

        ## Restart after wait period has passed
        # This ensures all file events have completed
        # by the time the command is restarted.
        if self.timer and self.timer.is_alive():
            self.timer.cancel()

        self.timer = Timer(self.wait, restart)
        self.timer.start()


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
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
        "-r", "--persist",
        action="store_true",
        help="continue watching files after the command exits"
    )
    parser.add_argument(
        "-i", "--ignore",
        action="append",
        nargs=1,
        help="ignore files matching the given pattern"
    )
    parser.add_argument(
        "-d", "--ignore-dir",
        action="store_true",
        help="ignore changes to directories"
    )
    parser.add_argument(
        "-o", "--only",
        action="append",
        nargs=1,
        help="only watch files matching the given pattern"
    )
    parser.add_argument(
        "-w", "--wait",
        type=float,
        nargs=1,
        default=0.5,
        help="a delay time (in seconds) to wait between file changes"
    )
    parser.add_argument(
        "--stdout",
        nargs=1,
        help="redirect stdout to this file"
    )
    parser.add_argument(
        "--stderr",
        nargs=1,
        help="redirect stderr to this file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        help="enable verbose output; use more v's for more verbosity"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s " + version
    )
    parser.add_argument("command")
    parser.add_argument("args", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    # Require a command
    if args.command is None:
        parser.error("Missing command.")

    # Get `path` arguments
    if args.path:
        paths = map(lambda x: x[0], args.path)
    else:
        # Or infer it from the command
        paths = [ os.path.expanduser(os.path.dirname(args.command)) ]

    ## Validate `path` arguments
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

    # Get stdout and stderr arguments
    stdout = None
    stderr = None
    if args.stdout:
        stdout = args.stdout[0]
    if args.stderr:
        stderr = args.stderr[0]

    # Get `ignore` arguments
    ignore = None
    if args.ignore:
        ignore = set(map(lambda x: x[0], args.ignore))
        if not ignore:
            ignore = None

    # Get `only` arguments
    only = None
    if args.only:
        only = set(map(lambda x: x[0], args.only))
        if not only:
            only = None

    # Get `wait` argument
    wait = args.wait
    if isinstance(wait, list):
        wait = wait[0]

    # Get command argument, and start the process
    runner = Runner([ args.command ] + args.args, stdout, stderr)

    # Start the watchdog observer thread
    event_handler = ChangeHandler(
        runner,
        wait,
        args.verbose,
        patterns=only,
        ignore_patterns=ignore,
        ignore_directories=args.ignore_dir
    )
    observer = Observer()
    for path in paths:
        observer.schedule(event_handler, path=path, recursive=True)
    observer.start()

    # Enter Rip Van Winkle mode
    try:
        while True:
            time.sleep(1)
            if (not args.persist) and (runner.poll() is not None):
                break
    except KeyboardInterrupt:
        pass

    print "\nrundogd is shutting down..."
    runner.terminate()
    observer.stop()
    observer.join()
