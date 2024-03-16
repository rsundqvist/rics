# Git

## Git fetch
Recipes for [git fetch](https://git-scm.com/docs/git-fetch).

### Prune branches
```bash
git fetch -p
```
Before fetching, remove any remote-tracking references that no longer exist on the remote.

## Git log
Recipes for [git log](https://git-scm.com/docs/git-log).

### Graph on the command line
```bash
git log --graph --oneline --decorate
```

### Files changed per commit between two dates
```bash
git log --before=2022-01 --until=2022-02 --name-only --pretty=format:"%hx09 -- %an%x09%ad%x09%s"
```

## Rebase
Recipes for [git rebase](https://git-scm.com/docs/git-rebase).

### Auto-fixup
Mark the commit as a fixup (for squash, use `--squash`) of a commit with hash `<bad-commit-hash>`.
```bash
git commit --fixup <ad-commit-hash>
git rebase -i <from-hash> --autosquash
```
This will create a message like `fixup! Bad-commit-subject-line`. When rebasing, all `!fixup`-commits will be moved and
merged into their "parent" commits automatically, assuming they are located after `<from-hash>`.

## Configuration
```bash
git config --global rerere.enabled true  # Remember merge conflict resolutions
git config --global column.ui auto  # Show >1 branch/row
git config --global branch.sort -committerdate  # default=alphabetical
```

## Links
* [So You Think You Know Git - FOSDEM 2024](https://www.youtube.com/watch?v=aolI_Rz0ZqY) for more.
