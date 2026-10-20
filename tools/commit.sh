#!/usr/bin/env bash
# Commits the published files, if anything changed, and pushes (rebasing onto newer pushes).
set -euo pipefail
cd "$(dirname "$0")/.."
git config user.name "github-actions"
git config user.email "github-actions@users.noreply.github.com"
git add -A index.json $(python -c "import json; print(' '.join(b['id'] for b in json.load(open('books.json'))))")
if git diff --cached --quiet; then echo "nothing new to publish"; exit 0; fi
git commit -m "$1"
git pull --rebase
git push
