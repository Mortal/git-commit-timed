#!/usr/bin/env python3


import argparse
import subprocess
import sys


def ls_tree(treeish):
    cmd = ("git", "ls-tree", "-r", treeish)
    output = subprocess.check_output(cmd, universal_newlines=True)
    return set(output.splitlines())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("commit")
    if sys.argv[1:]:
        commit = parser.parse_args().commit
    else:
        commit = "@"

    result_files = ls_tree(commit)
    first_files = ls_tree(commit + "^1")
    second_files = ls_tree(commit + "^2")

    merged = result_files - first_files - second_files
    unchanged = result_files & first_files & second_files
    from_first = (result_files - second_files) & first_files
    from_second = (result_files - first_files) & second_files
    deleted_during_merge = (first_files & second_files) - result_files
    deleted_from_first = first_files - result_files - second_files
    deleted_from_second = second_files - result_files - first_files

    # Venn diagram:
    assert (
        merged
        | unchanged
        | from_first
        | from_second
        | deleted_from_first
        | deleted_from_second
        == result_files | first_files | second_files
    )

    if not deleted_during_merge and not merged and not from_second:
        print("All %s changed files are from first parent" % len(from_first))
        return

    if not deleted_during_merge and not merged and not from_first:
        print("All %s changed files are from second parent" % len(from_second))
        return

    types = [
        ("++", merged),
        (" +", from_first),
        ("+ ", from_second),
        ("--", deleted_during_merge),
    ]
    output = ((entry, kind) for kind, entries in types for entry in entries)
    output = sorted(output, key=lambda x: x[0].split("\t")[1])
    for entry, kind in output:
        data, path = entry.split("\t")
        mode, type, hash = data.split()
        print("%s %s" % (kind, path))


if __name__ == "__main__":
    main()
