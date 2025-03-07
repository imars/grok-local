# grok_local/commands/git_commands.py
import logging
from ..utils import report

logger = logging.getLogger(__name__)

def handle_git_command(request, git_interface):
    req_lower = request.lower()
    if req_lower.startswith("git push"):
        parts = request.split()
        if len(parts) >= 4 and parts[2] == "origin":
            branch = parts[3]
            return report(git_interface.git_push(branch))
        return report("Error: Invalid git push command format. Use 'git push origin <branch>'")
    elif req_lower == "git status":
        return report(git_interface.git_status())
    elif req_lower == "git pull":
        return report(git_interface.git_pull())
    elif req_lower.startswith("git log"):
        count = request[7:].strip()
        count = int(count) if count.isdigit() else 1
        return report(git_interface.git_log(count))
    elif req_lower == "git branch":
        return report(git_interface.git_branch())
    elif req_lower.startswith("git checkout "):
        branch = request[12:].strip()
        return report(git_interface.git_checkout(branch))
    elif req_lower.startswith("git rm "):
        filename = request[6:].strip()
        return report(git_interface.git_rm(filename))
    elif req_lower.startswith("commit "):  # Moved from main handler
        full_message = request[6:].strip()
        if full_message.startswith("'") and full_message.endswith("'"):
            full_message = full_message[1:-1]
        elif full_message.startswith('"') and full_message.endswith('"'):
            full_message = full_message[1:-1]
        parts = full_message.split("|")
        message = parts[0] or "Automated commit"
        commit_message = full_message if len(parts) == 1 else message
        result = git_interface.commit_and_push(commit_message)
        if "failed" in result.lower():
            logger.error(result)
            return result
        return report(result)
    else:
        return f"Unknown git command: {request}"
