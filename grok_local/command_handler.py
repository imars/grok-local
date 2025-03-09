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
        
        if not command:
            return "No command provided. Use --help for options."
        
        if parsed_args.do:
            return execute_command(command, self.git_interface, self.ai_adapter, model=parsed_args.model)
        
        if command.startswith("git "):
            return git_commands.handle_git_command(command, self.git_interface)
        elif command.startswith(("create file ", "read file ", "write ", "append ", "delete file ")):
            return file_commands.file_command(command)
        elif command.startswith("checkpoint "):
            return checkpoint_commands.checkpoint_command(command, self.git_interface, use_git=True)
        elif command.startswith("bridge "):
            return bridge_commands.handle_bridge_command(command[7:], self.ai_adapter)
        elif command.startswith("copy "):
            return misc_commands.misc_command(command, self.ai_adapter, self.git_interface)
        elif command in ["list checkpoints", "what time is it", "version", "clean repo", "list files", "tree"]:
            return misc_commands.misc_command(command, self.ai_adapter, self.git_interface)
        else:
            return execute_command(command, self.git_interface, self.ai_adapter, model=parsed_args.model)

if __name__ == "__main__":
    from grok_local.tools import GitInterface, AIAdapter
    handler = CommandHandler(GitInterface(), AIAdapter())
    print(handler.handle())
