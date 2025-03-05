#!/usr/bin/env python3
# git_ops.py (in repo root)
import git
import logging
import os
from grok_local.config import PROJECT_DIR  # Import PROJECT_DIR

logger = logging.getLogger()

class GitInterface:
    def __init__(self, use_stub=False):
        self.use_stub = use_stub
        if not use_stub:
            self.repo = git.Repo(PROJECT_DIR)
        else:
            self.repo = None

    def git_status(self):
        if self.use_stub:
            return "Stubbed git status: nothing to report"
        return self.repo.git.status()

    def git_pull(self):
        if self.use_stub:
            return "Stubbed git pull: nothing pulled"
        return self.repo.git.pull()

    def git_log(self, count=1):
        if self.use_stub:
            return "Stubbed git log: no history"
        return self.repo.git.log('-n', str(count))

    def git_branch(self):
        if self.use_stub:
            return "Stubbed git branch: main"
        return self.repo.git.branch()

    def git_checkout(self, branch):
        if self.use_stub:
            return f"Stubbed checkout to {branch}"
        return self.repo.git.checkout(branch)

    def git_rm(self, filename):
        if self.use_stub:
            return f"Stubbed git rm: {filename}"
        return self.repo.git.rm(filename)

    def git_clean_repo(self):
        if self.use_stub:
            return "Stubbed git clean: repo cleaned"
        return self.repo.git.clean('-fd')

    def commit_and_push(self, message):
        if self.use_stub:
            return f"Stubbed commit and push: {message}"
        try:
            self.repo.git.add(all=True)
            self.repo.index.commit(message)
            self.repo.git.push('origin', self.repo.active_branch.name)
            return f"Committed and pushed: {message}"
        except Exception as e:
            logger.error(f"Commit and push failed: {str(e)}")
            return f"Failed to commit and push: {str(e)}"

    def git_push(self, branch):
        if self.use_stub:
            return f"Stubbed push to origin/{branch}"
        try:
            self.repo.git.push('origin', branch)
            return f"Pushed to origin/{branch} successfully"
        except Exception as e:
            logger.error(f"Git push failed: {str(e)}")
            return f"Failed to push to origin/{branch}: {str(e)}"

    def get_file_tree(self):
        """Return a string representation of the repo's file tree."""
        if self.use_stub:
            return "Stubbed file tree:\n- dir1/\n- file1.txt"
        try:
            # Use git ls-tree to get tracked files
            tree = self.repo.git.ls_tree('-r', '--name-only', 'HEAD')
            return "\n".join(sorted(tree.splitlines()))
        except Exception as e:
            logger.error(f"Failed to get file tree: {str(e)}")
            return f"Error getting file tree: {str(e)}"

def get_git_interface(use_stub=False):
    return GitInterface(use_stub=use_stub)
