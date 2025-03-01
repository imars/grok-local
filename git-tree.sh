#!/bin/bash
# Output a tree of files not ignored by Git
git ls-files --cached --others --exclude-standard | sort | while IFS= read -r line; do
  echo "$line" | awk -F'/' '{for (i=1; i<NF; i++) printf "  "; print $NF}'
done
