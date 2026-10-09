#!/usr/bin/env bash
# Concatenates all Java sources (without generated code in target/) into
# combined.txt in the repository root, each file preceded by a header line.
set -euo pipefail

cd "$(dirname "$0")"
out=combined.txt

find . -type f -name "*.java" -not -path "*/target/*" -not -path "./.git/*" -print0 |
    LC_ALL=C sort -z |
    while IFS= read -r -d '' file; do
        printf '\n--- File: %s ---\n\n' "$file"
        cat "$file"
    done > "$out"

echo "Wrote $out ($(grep -c '^--- File:' "$out") files)"
