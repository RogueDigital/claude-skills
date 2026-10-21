#!/usr/bin/env bash
# Repo checks: skill frontmatter, dashes, secret patterns, skill unit tests.
# No dependencies beyond bash, git, grep and python3. Exits non-zero on any failure.
set -u
cd "$(dirname "$0")/.."

fail=0
note() { echo "FAIL: $*"; fail=1; }

# 1. Skill frontmatter
shopt -s nullglob
count=0
for dir in skills/*/; do
  name=$(basename "$dir")
  file="$dir""SKILL.md"
  count=$((count + 1))
  if [ ! -f "$file" ]; then note "$dir has no SKILL.md"; continue; fi
  if [ "$(head -n 1 "$file")" != "---" ]; then note "$file has no frontmatter"; continue; fi
  front=$(awk 'NR==1{next} /^---[[:space:]]*$/{exit} {print}' "$file")
  fm_name=$(printf '%s\n' "$front" | sed -n 's/^name:[[:space:]]*//p' | head -n 1 | sed 's/^["'\'']//; s/["'\'']$//')
  if [ "$fm_name" != "$name" ]; then note "$file name '$fm_name' does not match folder '$name'"; fi
  desc=$(printf '%s\n' "$front" | awk '
    /^description:/ { sub(/^description:[[:space:]]*/, ""); if ($0 ~ /^[>|][-+]?[[:space:]]*$/) { folded=1; next } print; next }
    folded && /^[[:space:]]+/ { sub(/^[[:space:]]+/, ""); print; next }
    folded { folded=0 }')
  desc=$(printf '%s' "$desc" | tr '\n' ' ' | sed 's/^["'\'']//; s/[ "'\'']*$//')
  len=${#desc}
  if [ "$len" -lt 1 ] || [ "$len" -gt 1024 ]; then note "$file description length $len, need 1 to 1024"; fi
done
echo "skills checked: $count"

# 2. No em or en dash in tracked or new files
files=$(git ls-files --cached --others --exclude-standard)
if [ -n "$files" ]; then
  hits=$(printf '%s\n' "$files" | xargs -d '\n' grep -lP '[\x{2013}\x{2014}]' 2>/dev/null || true)
  if [ -n "$hits" ]; then note "em or en dash in: $hits"; fi

  # 3. Secret patterns (this script is excluded: it holds the patterns)
  scan=$(printf '%s\n' "$files" | grep -v '^scripts/check.sh$' || true)
  if [ -n "$scan" ]; then
    hits=$(printf '%s\n' "$scan" | xargs -d '\n' grep -lE 'sk-|ghp_|gho_|AKIA|re_[A-Za-z0-9]{8}|-----BEGIN' 2>/dev/null || true)
    if [ -n "$hits" ]; then note "possible secret in: $hits"; fi
  fi
fi

# 4. Unit tests per skill
for dir in skills/*/; do
  if [ -d "$dir""tests" ]; then
    echo "tests: $dir"
    (cd "$dir" && python3 -m unittest discover) || note "tests failed in $dir"
  fi
done

if [ "$fail" -eq 0 ]; then echo "check: ok"; else echo "check: FAILED"; fi
exit "$fail"
