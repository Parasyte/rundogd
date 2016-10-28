# `rundogd`

## About `rundogd`

Pronounced "run dogged".

`rundogd` is a filesystem watcher-restarter daemon. Its main task is watching a path on the filesystem for any changes (files and folders created, deleted, moved, and modified) and automagically restarts the provided command on any of these events.

## Getting `rundogd`

`rundogd` source code is hosted on bitbucket::

    $ git clone https://bitbucket.org/parasyte/rundogd.git

### Dependencies

* [Python](http://www.python.org/) 2.6+
* [watchdog](http://pypi.python.org/pypi/watchdog) 0.5.4+

## Usage

    usage: rundogd [options] command

    Filesystem watcher-restarter daemon.

    optional arguments:
      -h, --help            show this help message and exit
      -p PATH, --path PATH  recursively watch for file changes in this path
      -r, --persist         continue watching files after the command exits
      -i IGNORE, --ignore IGNORE
                            ignore files matching the given pattern
      -d, --ignore-dir      ignore changes to directories
      -o ONLY, --only ONLY  only watch files matching the given pattern
      -w WAIT, --wait WAIT  a delay time (in seconds) to wait between file changes
      --stdout STDOUT       redirect stdout to this file
      --stderr STDERR       redirect stderr to this file
      -v, --verbose         enable verbose output; use more v's for more verbosity
      --version             show program's version number and exit

`rundogd` takes one optional argument (`-p`) to specify the path that it will watch. Use `-p` multiple times to watch a list of paths. If omitted, the path will be inferred from the command, or it will use the current working directory.

The `-i` switch can be used to ignore file patterns. And `-o` is used to watch only specific file patterns.

## Examples

    $ ./rundogd -p src/data python src/main.py

Starts `python src/main.py` and restarts it every time any files are changed in the directory `src/data`.

----

    $ ./rundogd -p src/data -p src/tmp python src/main.py

Starts `python src/main.py` and restarts it every time any files are changed in the directories `src/data` or `src/tmp`.

----

    $ ./rundogd -p src/data -p src/tmp -i '*.pyc' python src/main.py

Starts `python src/main.py` and restarts it every time any files are changed in the directories `src/data` or `src/tmp`, except for \*.pyc files, which are automatically regenerated when starting Python after the source files have changed. This can be used to prevent a "double startup" when working on Python.

----

    $ ./rundogd /home/me/src/program

Starts `/home/me/src/program` and restarts it every time any files are changed in the directory `/home/me/src`.

----

    $ ./rundogd -r ls -al

Starts ``ls -al`` and restarts it every time any files are changed in the
current working directory. Uses the ``persist`` option to continue watching for
file changes even after ``ls`` exits.

## Recipes

Git repos are updated often, even when doing a `git status`. This will help:

    -i '*/.git/*'

----

Python developers should ignore the files that Python compiles automatically:

    -i '*.pyc' -i '*.pyo'

----

When developing on Mac OS X on non-HFS file systems, the following patterns will ignore the special files that get created and updated automatically:

    -i '.DS_Store' -i '.Trashes' -i '._*'

----

Similar special files on Windows:

    -i 'Thumbs.db' -i 'desktop.ini'
