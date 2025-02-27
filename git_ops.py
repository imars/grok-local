import os
import git
from git import Repo
import logging

PROJECT_DIR = os.getcwd()
logger = logging.getLogger(__name__)

def git_status():
    try:
        repo = Repo(PROJECT_DIR)
        status = repo.git.status()
        logger.info("Retrieved git status")
        return status
    except Exception as e:
        logger.error(f"Git status error: {e}")
        return f"Git status error: {e}"

def git_pull():
    try:
        repo = Repo(PROJECT_DIR)
        repo.git.pull()
        logger.info("Pulled latest changes")
        return "Pulled latest changes"
    except Exception as e:
        logger.error(f"Git pull error: {e}")
        return f"Git pull error: {e}"

def git_log(count=1):
    try:
        repo = Repo(PROJECT_DIR)
        log = repo.git.log(f"-{count}")
        logger.info(f"Retrieved git log with count {count}")
        return log
    except Exception as e:
        logger.error(f"Git log error: {e}")
        return f"Git log error: {e}"

def git_branch():
    try:
        repo = Repo(PROJECT_DIR)
        branches = repo.git.branch()
        logger.info("Listed git branches")
        return branches
    except Exception as e:
        logger.error(f"Git branch error: {e}")
        return f"Git branch error: {e}"

def git_checkout(branch):
    try:
        repo = Repo(PROJECT_DIR)
        repo.git.checkout(branch)
        logger.info(f"Checked out branch: {branch}")
        return f"Checked out branch: {branch}"
    except Exception as e:
        logger.error(f"Git checkout error: {e}")
        return f"Git checkout error: {e}"

def git_commit_and_push(message="Automated commit"):
    repo = Repo(PROJECT_DIR)
    try:
        repo.git.add(A=True)
        status = repo.git.status()
        if "nothing to commit" in status:
            logger.info("Nothing to commit")
            return "Nothing to commit"
        repo.git.commit(m=message)
        repo.git.push()
        logger.info(f"Committed and pushed: {message}")
        return f"Committed and pushed: {message}"
    except git.GitCommandError as e:
        logger.error(f"Git error: {e}")
        return f"Git error: {str(e)}"

def git_rm(filename):
    try:
        repo = Repo(PROJECT_DIR)
        repo.git.rm(filename)
        logger.info(f"Removed file from git: {filename}")
        return f"Removed file from git: {filename}"
    except git.GitCommandError as e:
        logger.error(f"Git rm error for {filename}: {e}")
        return f"Git rm error: {str(e)}"
