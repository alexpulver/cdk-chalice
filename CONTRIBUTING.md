# Contributing to cdk-chalice

:+1::tada: First off, thanks for taking the time to contribute! :tada::+1:

The following is a set of guidelines for contributing to `cdk-chalice`. These are mostly 
guidelines, not rules. Use your best judgment, and feel free to propose changes to this 
document in a pull request.

## Contributor

### Create development environment
```bash
git clone https://github.com/alexpulver/cdk-chalice.git
cd cdk-chalice
python3 -m venv .venv
source .venv/bin/activate
./scripts/install-deps.sh
git checkout -b BRANCH
```

### [Optional] Add dependencies (ordered by constraints)
```bash
<add dependencies to setup.py or requirements-dev.in>
pip-compile
pip-compile requirements-dev.in
./scripts/install-deps.sh
./scripts/run-tests.sh
```

### [Optional] Upgrade dependencies  (ordered by constraints)
```bash
pip-compile --upgrade
pip-compile --upgrade requirements-dev.in
./scripts/install-deps.sh
./scripts/run-tests.sh
```

### Implement
```bash
<hack>
./scripts/run-tests.sh
git commit [OPTIONS] [ARGS]...
```

### [Optional] Update CHANGELOG.md if your change affects library interface
```bash
changelog [OPTIONS] COMMAND [ARGS]...
git commit -m 'Update CHANGELOG.md' CHANGELOG.md
```

### Submit pull request
```bash
git push --set-upstream origin BRANCH
<open pull request>
<pull request merged and remote branch deleted>
git checkout master
git pull --rebase
git remote prune origin
git branch -D BRANCH
```

## Maintainer
```bash
git checkout master
git pull --rebase
changelog current
changelog suggest
./scripts/bump-version.sh [ARGS]  # Bump based on change from current to suggested version
git push
git push --tags
```
