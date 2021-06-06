# Contributing to cdk-chalice

:+1::tada: First off, thanks for taking the time to contribute! :tada::+1:

The following is a set of guidelines for contributing to `cdk-chalice`. These are mostly 
guidelines, not rules. Use your best judgment, and feel free to propose changes to this 
document in a pull request.

## Contributor

**Environment**

```bash
git clone https://github.com/alexpulver/cdk-chalice.git
cd cdk-chalice
python3 -m venv .venv
source .venv/bin/activate
pip install pip-tools==6.1.0
pip-sync requirements.txt requirements-dev.txt
git checkout -b branch-name
```

**Upgrading dependencies**

```bash
pip-compile --upgrade
pip-compile --upgrade requirements-dev.in
pip-sync requirements.txt requirements-dev.txt
```

**Implementation**

```bash
<hack>
./scripts/run-tests.sh
git commit [OPTIONS] [ARGS]...
```

**Optional:** Use whenever you commit a change that affects how end users use cdk-chalice

```bash
changelog [OPTIONS] COMMAND [ARGS]...
git commit -m 'Update CHANGELOG.md' CHANGELOG.md
```

```bash
git push
<open pull request>
<pull request merged and remote branch deleted>
git checkout master
git remote prune origin
git branch -D branch-name
```

## Owner

``` bash
git checkout master
git pull --rebase
changelog current
changelog suggest
<bump version based on change from current to suggested version>
./scripts/bump-version.sh [ARGS]
git push
git push --tags
```
