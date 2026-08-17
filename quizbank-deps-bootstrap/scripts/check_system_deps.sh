#!/usr/bin/env bash
set -euo pipefail
need() { command -v "$1" >/dev/null || missing+="$1\n"; }

missing=""
echo "Checking system tools…"

# Core
for c in python3 git pre-commit jq yq; do need "$c"; done

# Document/build tools commonly used in this project family
for c in typst pandoc tectonic; do need "$c"; done

# Useful extras
for c in graphviz dot zip unzip convert; do need "$c"; done

if [ -n "$missing" ]; then
  echo -e "\nMissing system tools (install via your package manager):\n$missing"
  exit 1
fi

echo "All required system tools found."
