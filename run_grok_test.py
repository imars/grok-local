import subprocess
import time

# Commands for the mini project workflow test
commands = [
    "create file plan.txt",
    "write Initial project plan to plan.txt",
    "copy file plan.txt to plan_v1.txt",
    "write Updated project plan v1 to plan_v1.txt",
    "rename file plan.txt to plan_original.txt",
    "what time is it",
    "commit Project plan versioned at {time}",
    "list files",
    "git status"
]

def run_grok_test():
    # Start grok_local.py in interactive mode with unbuffered output
    process = subprocess.Popen(
        ["python", "-u", "grok_local.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line-buffered
    )

    # Feed commands and capture full output
    output = []
    commit_time = None
    for cmd in commands:
        process.stdin.write(cmd + "\n")
        process.stdin.flush()
        time.sleep(1)  # Wait for command to process
        cmd_output = ""
        # Read until we hit the next Command: prompt or timeout
        start_time = time.time()
        while time.time() - start_time < 2:  # 2-second timeout
            line = process.stdout.readline().strip()
            if not line or "Command:" in line:
                break
            cmd_output += line + "\n"
        cmd_output = cmd_output.strip()
        if "what time is it" in cmd:
            commit_time = cmd_output
            output.append(f"{cmd}: {cmd_output}")
        elif "commit" in cmd and "{time}" in cmd:
            full_cmd = cmd.format(time=commit_time)
            process.stdin.write(full_cmd + "\n")
            process.stdin.flush()
            time.sleep(1)
            commit_output = ""
            start_time = time.time()
            while time.time() - start_time < 2:
                line = process.stdout.readline().strip()
                if not line or "Command:" in line:
                    break
                commit_output += line + "\n"
            commit_output = commit_output.strip()
            output.append(f"{full_cmd}: {commit_output}")
        else:
            output.append(f"{cmd}: {cmd_output}")

    # Exit interactive mode
    process.stdin.write("exit\n")
    process.stdin.flush()
    time.sleep(1)

    # Wait for process to finish and get remaining output
    stdout, stderr = process.communicate()
    if stderr:
        output.append(f"Errors: {stderr}")

    # Print results
    for line in output:
        print(line)

if __name__ == "__main__":
    run_grok_test()
