#!/bin/bash
# Auto-commit hook: commits changes after Claude edits/writes files

# Exit if no changes
if [ -z "$(git -C "$CLAUDE_PROJECT_DIR" status --porcelain)" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"
git add -A
git commit -m "Auto-commit: $(date '+%Y-%m-%d %H:%M:%S')

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
exit 0
