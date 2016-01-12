git commit-timed - commit using time of changed files
=====================================================

`git-commit-timed` is a wrapper around `git commit` that sets
the author timestamp to the modification time of the files to be committed
(using the `--date` argument).
If multiple files are to be committed, the most recent mtime is used.

To use the command, download the script, set it as executable and add it as a
global Git alias:

```
$ git clone https://github.com/Mortal/git-commit-timed.git
$ git config --global alias.commit-timed /path/to/git-commit-timed/git-commit-timed
```
