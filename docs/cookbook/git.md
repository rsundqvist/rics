# Git

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
Mark commits at fixups (or squash; `--squash`) for a commit with hash `<hash>`.
```bash
git commit --fixup <hash>
git rebase -i --autosquash
```
