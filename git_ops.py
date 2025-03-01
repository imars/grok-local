import git
import time
import logging

# Setup basic logging (compatible with grok_local.py --debug flag)
logging.basicConfig(level=logging.INFO, filename="grok_local.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

def git_status() -> str:
    repo = git.Repo(".")
    return repo.git.status()

def git_pull() -> str:
    repo = git.Repo(".")
    return repo.git.pull()

def git_log(count: int = 1) -> str:
    repo = git.Repo(".")
    return repo.git.log(f"-{count}")

def git_branch() -> str:
    repo = git.Repo(".")
    return repo.git.branch()

def git_checkout(branch: str) -> str:
    repo = git.Repo(".")
    return repo.git.checkout(branch)

def git_rm(filename: str) -> str:
    repo = git.Repo(".")
    return repo.git.rm(filename)

def git_clean_repo() -> str:
    repo = git.Repo(".")
    return repo.git.clean("-fd")

def git_commit_and_push(message: str) -> str:
    """
    Commits changes and pushes to remote with retry logic for robustness.
    Args:
        message: Commit message
    Returns:
        str: Success message or error details
    """
    repo = git.Repo(".")
    max_retries = 3
    initial_delay = 1  # seconds

    # Stage all changes
    repo.git.add(A=True)
    repo.git.commit(m=message)
    logging.info(f"Committed changes with message: {message}")

    # Retry logic for push
    for attempt in range(max_retries):
        try:
            repo.git.push()
            logging.info("Successfully pushed to remote")
            return "Committed and pushed successfully"
        except git.GitCommandError as e:
            logging.error(f"Push failed on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt == max_retries - 1:
                return f"Failed to push after {max_retries} attempts: {str(e)}"
            delay = initial_delay * (2 ** attempt)  # Exponential backoff
            logging.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)

    return "Unexpected error in git_commit_and_push"  # Fallback (shouldn't hit)

if __name__ == "__main__":
    # Example usage for testing
    print(git_commit_and_push("Test commit with retry logic"))
