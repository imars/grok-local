import argparse
import sys
from grok_local.commands import git_commands, file_commands, checkpoint_commands, bridge_commands, misc_commands
from grok_local.tools import execute_command

class CommandHandler:
    def __init__(self, git_interface, ai_adapter):
        self.git_interface = git_interface
        self.ai_adapter = ai_adapter
        self.parser = argparse.ArgumentParser(description="Grok Local CLI")
        self.parser.add_argument("command", nargs="*", help="Command to execute")
        self.parser.add_argument("--do", action="store_true", help="Execute command directly")
        self.parser.add_argument("--model", help="Specify model for inference")

    def handle(self, args=None):
        if args is None:
            args = sys.argv[1:]
        
        parsed_args = self.parser.parse_args(args)
        command = " ".join(parsed_args.command).strip().lower()
        print(f"Debug: Handling command: '{command}'", file=sys.stderr)
        
        if not command:
            return "No command provided. Use --help for options."
        
        if parsed_args.do:
            print(f"Debug: Using execute_command for '{command}'", file=sys.stderr)
            return execute_command(command, self.git_interface, self.ai_adapter, model=parsed_args.model)
        
        misc_keywords = ["what time is it", "version", "clean repo", "list files", "tree", "copy"]
        if any(kw in command for kw in misc_keywords):
            print(f"Debug: Routing to misc_commands for '{command}'", file=sys.stderr)
            return misc_commands.misc_command(command, self.ai_adapter, self.git_interface)
        elif command.startswith("git "):
            print(f"Debug: Routing to git_commands for '{command}'", file=sys.stderr)
            return git_commands.handle_git_command(command, self.git_interface)
        elif command.startswith(("create file ", "read file ", "write ", "append ", "delete file ")):
            print(f"Debug: Routing to file_commands for '{command}'", file=sys.stderr)
            return file_commands.file_command(command)
        elif command.startswith("checkpoint "):
            print(f"Debug: Routing to checkpoint_commands for '{command}'", file=sys.stderr)
            return checkpoint_commands.checkpoint_command(command, self.git_interface, use_git=True)
        elif command.startswith("bridge "):
            print(f"Debug: Routing to bridge_commands for '{command}'", file=sys.stderr)
            return bridge_commands.handle_bridge_command(command[7:], self.ai_adapter)
        else:
            print(f"Debug: Fallback to execute_command for '{command}'", file=sys.stderr)
            return execute_command(command, self.git_interface, self.ai_adapter, model=parsed_args.model)

if __name__ == "__main__":
    from grok_local.tools import GitInterface, AIAdapter
    handler = CommandHandler(GitInterface(), AIAdapter())
    print(handler.handle())
