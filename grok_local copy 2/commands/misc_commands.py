# grok_local/commands/misc_commands.py
import logging
import os
from ..config import PROJECT_DIR, LOCAL_DIR
from ..utils import what_time_is_it, report
from file_ops import list_files, clean_cruft, write_file, move_file

logger = logging.getLogger(__name__)

def handle_misc_command(request, ai_adapter, git_interface):
    req_lower = request.lower()
    if req_lower in ["what time is it", "ask what time is it"]:
        return report(what_time_is_it())
    elif req_lower == "version":
        return report("grok-local v0.1")
    elif req_lower == "clean repo":
        cruft_result = clean_cruft()
        git_result = git_interface.git_clean_repo()
        return report(f"{cruft_result}\n{git_result}")
    elif req_lower == "list files":
        return report(list_files())
    elif req_lower.startswith("create spaceship fuel script"):
        response = ai_adapter.delegate("Generate a Python script simulating a spaceship's fuel consumption.")
        if "Error" not in response:
            filename = "spaceship_fuel.py"
            logger.info(f"Generated script:\n{response}")
            write_file(filename, response.strip(), path=LOCAL_DIR)
            git_interface.commit_and_push(f"Added {filename} from AI in local/")
            return report(f"Created {filename} with fuel simulation script in local/ directory.")
        return report(response)
    elif req_lower.startswith("create x login stub"):
        response = ai_adapter.delegate("Generate a Python script that simulates an X login process as a stub for x_poller.py...")
        if "Error" not in response:
            filename = "local/x_login_stub.py"
            logger.info(f"Generated X login stub:\n{response}")
            write_file(filename, response.strip(), path=None)
            move_file("x_login_stub.py", "x_login_stub.py", src_path=PROJECT_DIR, dst_path=LOCAL_DIR)
            git_interface.commit_and_push("Added X login stub for testing")
            return report(f"Created {filename} with X login stub and committed.")
        return report(response)
    else:
        return f"Unknown misc command: {request}"
