import os
import git
import logging
import time

PROJECT_DIR = os.getcwd()
LOG_FILE = os.path.join(PROJECT_DIR, "grok_local.log")

logger = logging.getLogger(__name__)

def git_status():
    try:
        repo = git.Repo(PROJECT_DIR)
        status = repo.git.status()
        logger.info("Git status retrieved")
        return status
    except Exception as e:
        logger.error(f"Git status failed: {e}")
        return f"Error: {e}"

def git_pull():
    try:
        repo = git.Repo(PROJECT_DIR)
        origin = repo.remote(name="origin")
        origin.pull()
        logger.info("Git pull successful")
        return "Pulled latest changes from remote"
    except Exception as e:
        logger.error(f"Git pull failed: {e}")
        return f"Error: {e}"

def git_log(count=1):
    try:
        repo = git.Repo(PROJECT_DIR)
        log = repo.git.log(f"-{count}", oneline=True)
        logger.info(f"Git log retrieved for last {count} commits")
        return log
    except Exception as e:
        logger.error(f"Git log failed: {e}")
        return f"Error: {e}"

def git_branch():
    try:
        repo = git.Repo(PROJECT_DIR)
        branches = repo.git.branch()
        logger.info("Git branches retrieved")
        return branches
    except Exception as e:
        logger.error(f"Git branch failed: {e}")
        return f"Error: {e}"

def git_checkout(branch):
    try:
        repo = git.Repo(PROJECT_DIR)
        repo.git.checkout(branch)
        logger.info(f"Checked out branch: {branch}")
        return f"Checked out {branch}"
    except Exception as e:
        logger.error(f"Git checkout failed: {e}")
        return f"Error: {e}"

def git_rm(filename):
    try:
        repo = git.Repo(PROJECT_DIR)
        repo.git.rm(filename)
        logger.info(f"Removed file from Git: {filename}")
        return f"Removed {filename} from Git tracking"
    except Exception as e:
        logger.error(f"Git rm failed: {e}")
        return f"Error: {e}"

def git_clean_repo():
    try:
        repo = git.Repo(PROJECT_DIR)
        repo.git.clean("-f", "-d")
        logger.info("Cleaned untracked files from repo")
        return "Cleaned untracked files from repo"
    except Exception as e:
        logger.error(f"Git clean failed: {e}")
        return f"Error: {e}"

def git_commit_and_push(message, retries=3, delay=5):
    """Commit and push changes with retries on failure."""
    try:
        repo = git.Repo(PROJECT_DIR)
        repo.git.add(all=True)
        if repo.is_dirty():
            repo.git.commit(m=message)
            logger.info(f"Committed changes: {message}")
        else:
            logger.info("No changes to commit")
            return "No changes to commit"

        for attempt in range(retries):
            try:
                origin = repo.remote(name="origin")
                origin.push()
                logger.info(f"Pushed changes: {message}")
                return f"Committed and pushed: '{message}'"
            except git.GitCommandError as e:
                logger.warning(f"Push attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    logger.error(f"Push failed after {retries} retries: {e}")
                    return f"Error pushing after {retries} retries: {e}"
    except Exception as e:
        logger.error(f"Git commit/push failed: {e}")
        return f"Error: {e}"

if __name__ == "__main__":
    print(git_status())
