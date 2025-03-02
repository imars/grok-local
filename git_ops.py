import os
import time
from git import Repo
import logging

# Ensure logging is configured
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("grok_local.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def git_status() -> str:
    repo = Repo(os.getcwd())
    return repo.git.status()

def git_pull() -> str:
    repo = Repo(os.getcwd())
    return repo.git.pull()

def git_log(count: int = 1) -> str:
    repo = Repo(os.getcwd())
    return repo.git.log(f'-{count}')

def git_branch() -> str:
    repo = Repo(os.getcwd())
    return repo.git.branch()

def git_checkout(branch: str) -> str:
    repo = Repo(os.getcwd())
    return repo.git.checkout(branch)

def git_rm(filename: str) -> str:
    repo = Repo(os.getcwd())
    return repo.git.rm(filename)

def git_clean_repo() -> str:
    repo = Repo(os.getcwd())
    return repo.git.clean('-fd')

def git_commit_and_push(message: str) -> str:
    repo = Repo(os.getcwd())
    max_attempts = 3
    delay = 2  # seconds between retries
    
    # Explicitly stage all changes in the working directory
    repo.git.add(all=True)  # Stage all changes, including test_network_failure.unique
    logger.debug(f"Staged files after add: {repo.git.diff('--cached', '--name-only')}")

    # Debug: Log Git state
    logger.debug(f"Git status before commit: {repo.git.status()}")
    logger.debug(f"Staged files before commit: {repo.git.diff('--cached', '--name-only')}")

    try:
        repo.git.commit('-m', message)
        logger.info(f"Committed changes with message: '{message}'")
    except Exception as e:
        logger.error(f"Commit failed: {e}")
        return f"Commit failed: {e}"

    for attempt in range(max_attempts):
        try:
            logger.info(f"Push attempt {attempt + 1}/{max_attempts} for commit: '{message}'")
            repo.git.push()
            logger.info("Successfully pushed to remote")
            return "Commit and push successful"
        except Exception as e:
            logger.warning(f"Push attempt {attempt + 1}/{max_attempts} failed: {e}")
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                logger.error(f"Push failed after {max_attempts} attempts: {e}")
                return f"Push failed after {max_attempts} attempts: {e}"

if __name__ == "__main__":
    print(git_commit_and_push("Test commit"))
