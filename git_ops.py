import os
import time
from git import Repo
import logging
import subprocess
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("grok_local.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Abstract Git Interface
class GitInterface(ABC):
    @abstractmethod
    def commit_and_push(self, message):
        pass

    @abstractmethod
    def status(self):
        pass

    @abstractmethod
    def pull(self):
        pass

    @abstractmethod
    def log(self, count=1):
        pass

    @abstractmethod
    def branch(self):
        pass

    @abstractmethod
    def checkout(self, branch):
        pass

    @abstractmethod
    def rm(self, filename):
        pass

    @abstractmethod
    def clean_repo(self):
        pass

    @abstractmethod
    def get_file_tree(self):
        pass

# Stub Implementation
class StubGit(GitInterface):
    def commit_and_push(self, message):
        logger.debug(f"Stubbed git commit and push: {message}")
        return "Stubbed Git commit successful"

    def status(self):
        return "Stubbed git status"

    def pull(self):
        return "Stubbed git pull"

    def log(self, count=1):
        return f"Stubbed git log (-{count})"

    def branch(self):
        return "Stubbed git branch"

    def checkout(self, branch):
        return f"Stubbed git checkout {branch}"

    def rm(self, filename):
        return f"Stubbed git rm {filename}"

    def clean_repo(self):
        return "Stubbed git clean -fd"

    def get_file_tree(self):
        logger.debug("Returning stubbed Git file tree")
        return "Repository File Tree (stubbed):\n  .gitignore\n  grok_local.py\n  x_poller.py"

# Real Implementation
class RealGit(GitInterface):
    def __init__(self):
        self.repo = Repo(os.getcwd())

    def commit_and_push(self, message):
        try:
            self.repo.git.add(".")
            logger.debug(f"Staged files: {self.repo.git.diff('--cached', '--name-only')}")
            if not self.repo.is_dirty():
                logger.info("Nothing to commit")
                return "Nothing to commit"
            self.repo.git.commit('-m', message)
            logger.info(f"Committed changes with message: '{message}'")
        except Exception as e:
            logger.error(f"Commit failed: {e}")
            return f"Commit failed: {e}"

        max_attempts = 3
        delay = 1
        for attempt in range(max_attempts):
            try:
                logger.info(f"Push attempt {attempt + 1}/{max_attempts} for commit: '{message}'")
                self.repo.git.push()
                logger.info("Successfully pushed to remote")
                return "Commit and push successful"
            except Exception as e:
                logger.warning(f"Push attempt {attempt + 1}/{max_attempts} failed: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                else:
                    logger.error(f"Push failed after {max_attempts} attempts: {e}")
                    return f"Push failed after {max_attempts} attempts: {e}"

    def status(self):
        return self.repo.git.status()

    def pull(self):
        return self.repo.git.pull()

    def log(self, count=1):
        return self.repo.git.log(f'-{count}')

    def branch(self):
        return self.repo.git.branch()

    def checkout(self, branch):
        return self.repo.git.checkout(branch)

    def rm(self, filename):
        return self.repo.git.rm(filename)

    def clean_repo(self):
        return self.repo.git.clean('-fd')

    def get_file_tree(self):
        logger.debug("Fetching real Git file tree")
        try:
            result = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                capture_output=True, text=True, check=True
            )
            files = result.stdout.splitlines()
            files.sort()
            tree_lines = []
            for file in files:
                parts = file.split('/')
                indent = "  " * (len(parts) - 1)
                tree_lines.append(f"{indent}{parts[-1]}")
            return "Repository File Tree (tracked and untracked, not ignored):\n" + "\n".join(tree_lines)
        except subprocess.CalledProcessError as e:
            return f"Error generating Git file tree: {e}"
        except Exception as e:
            return f"Unexpected error generating Git file tree: {e}"

def get_git_interface(use_stub=True):
    return StubGit() if use_stub else RealGit()

# Existing functions updated to use interface
def git_commit_and_push(message):
    git_interface = get_git_interface(use_stub=False)  # Default to real for direct calls
    return git_interface.commit_and_push(message)

def git_status():
    return get_git_interface(use_stub=False).status()

def git_pull():
    return get_git_interface(use_stub=False).pull()

def git_log(count=1):
    return get_git_interface(use_stub=False).log(count)

def git_branch():
    return get_git_interface(use_stub=False).branch()

def git_checkout(branch):
    return get_git_interface(use_stub=False).checkout(branch)

def git_rm(filename):
    return get_git_interface(use_stub=False).rm(filename)

def git_clean_repo():
    return get_git_interface(use_stub=False).clean_repo()

if __name__ == "__main__":
    print(git_commit_and_push("Test commit"))
