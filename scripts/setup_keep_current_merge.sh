#!/usr/bin/env bash
set -euo pipefail

git config merge.keep-current.name "Always keep the current branch version"
git config merge.keep-current.driver true
git config merge.keep-current.recursive binary

echo "Configured merge.keep-current for $(git rev-parse --show-toplevel)"
echo "Files matched by .gitattributes will now auto-accept the current branch during merges."
