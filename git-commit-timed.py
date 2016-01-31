#!/usr/bin/env python3


import os
import re
import shlex
import argparse
import datetime
import subprocess


class UnmergedFiles(Exception):
    pass


def get_git_status():
    p = subprocess.Popen(
        ('git', 'status', '--porcelain'),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        universal_newlines=True)
    with p:
        stdout, _stderr = p.communicate()
    pattern = (
        r'^(?P<X>[ MADRCU?!])(?P<Y>[ MADU?!]) ' +
        r'(?:(?P<from>"(?:\\.|[^"]+)*"|[^ ]+) -> )?' +
        r'(?P<to>"(?:\\.|[^"]+)*"|[^ ]+)$')

    untracked = set()
    auto_add = set()
    staged = set()
    unmerged = set()
    unchanged = set()
    ignored = set()

    for i, line in enumerate(stdout.splitlines()):
        mo = re.match(pattern, line, re.M)
        if mo is None:
            raise ValueError(
                "Could not parse line %d: %r" %
                (i + 1, line))
        index = mo.group('X')
        worktree = mo.group('Y')
        filename, = shlex.split(mo.group('to'))
        if 'U' in (index, worktree):
            unmerged.add(filename)
        elif (index, worktree) in (('D', 'D'), ('A', 'A')):
            # both deleted/both added
            unmerged.add(filename)
        elif index == '?':
            untracked.add(filename)
        elif index == '!':
            ignored.add(filename)
        elif index == ' ':
            if worktree != ' ':
                auto_add.add(filename)
            else:
                unchanged.add(filename)
        else:
            staged.add(filename)

    if ignored:
        raise ValueError("git status reported ignored file(s) %r" %
                         (sorted(ignored),))
    if unmerged:
        raise UnmergedFiles("unmerged file(s) in tree: %r" %
                            (sorted(unmerged),))
    return staged, auto_add


def get_mtime(filename):
    return os.stat(filename).st_mtime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', '-a', action='store_true')
    parser.add_argument('--message', '-m', default=None)
    parser.add_argument('filename', nargs='*')
    args = parser.parse_args()

    git_prefix = os.environ.get('GIT_PREFIX', '')
    filenames = [git_prefix + f for f in args.filename]

    if args.all and args.filename:
        parser.error("Paths with -a does not make sense.")

    try:
        staged, auto_add = get_git_status()
    except UnmergedFiles as exn:
        parser.error(exn.args[0])

    if args.all:
        staged |= auto_add

    staged |= set(filenames)

    if not staged:
        parser.error("no changes added to commit")

    try:
        mtime = max(get_mtime(f) for f in staged)
    except FileNotFoundError as exn:
        parser.error(str(exn))

    commit_time = datetime.datetime.fromtimestamp(mtime)

    commit_cmdline = (
        ('git', 'commit') +
        ('--date', commit_time.isoformat()) +
        (('-a',) if args.all else ()) +
        (('-m', args.message) if args.message is not None else ()) +
        ('--',) + tuple(filenames))
    try:
        subprocess.check_call(commit_cmdline)
    except subprocess.CalledProcessError as exn:
        raise SystemExit(exn.returncode)


if __name__ == "__main__":
    main()
