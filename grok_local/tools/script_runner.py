import subprocess
import sys
from .logging import log_conversation

def debug_script(script_path, debug=False):
    """Run a Python script and return its output or error trace."""
    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            output = result.stdout
            if debug:
                print(f"Debug: Script ran successfully: {output}", file=sys.stderr)
            log_conversation(f"Debug script {script_path}: Success - {output}")
            return output
        else:
            error = result.stderr
            if debug:
                print(f"Debug: Script failed: {error}", file=sys.stderr)
            log_conversation(f"Debug script {script_path}: Error - {error}")
            return f"Error: {error}"
    except subprocess.TimeoutExpired:
        error = "Error: Script execution timed out after 30s"
        if debug:
            print(f"Debug: {error}", file=sys.stderr)
        log_conversation(f"Debug script {script_path}: {error}")
        return error
    except Exception as e:
        error = f"Error: Failed to run script: {str(e)}"
        log_conversation(f"Debug script {script_path}: {error}")
        return error
