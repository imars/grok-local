from .task import Task
from .memory import Memory
from ..agents import DeveloperAgent, DebuggerAgent, DesignerAgent, UserAgent
from ..tools.script_runner import debug_script
from ..tools.logging import log_conversation
from datetime import datetime

class Orchestrator:
    def __init__(self):
        self.memory = Memory()
        self.agents = {
            "developer": DeveloperAgent(),
            "debugger": DebuggerAgent(),
            "designer": DesignerAgent(),
            "user": UserAgent()
        }

    def run_task(self, initial_task: str, max_iterations=3, debug=False, model=None):
        task = Task(description=initial_task, agent_role="developer")
        # Model selection: Passed model > complexity > default
        if model:
            effective_model = model
        elif any(kw in initial_task.lower() for kw in ["factorial", "list", "add", "reverse"]):
            effective_model = "llama3.2:latest"  # Simple
        elif any(kw in initial_task.lower() for kw in ["game", "clone", "pygame", "script"]):
            effective_model = "deepseek-r1:8b"  # Moderate
        elif any(kw in initial_task.lower() for kw in ["3d", "universe", "persistent", "trade", "avatar"]):
            effective_model = "grok3" if "grok3" in os.environ.get("AVAILABLE_MODELS", "") else "deepseek-r1:8b"  # Advanced
        else:
            effective_model = "deepseek-r1:8b"  # Default moderate
        if debug:
            log_conversation(f"Orchestrator: Using model {effective_model} for task: {initial_task}")
        self.agents["developer"].model = effective_model
        self.agents["debugger"].model = effective_model
        code = self.agents["developer"].run(task, self.memory)
        if debug:
            log_conversation(f"Orchestrator: Developer returned code at {datetime.now()}: {code}")
        code = code.strip().replace("", "").strip()
        script_path = "grok_local/projects/output.py"
        with open(script_path, "w") as f:
            f.write(code)
        if "fix" in initial_task.lower():
            for _ in range(max_iterations):
                debug_result = debug_script(script_path, debug)
                if "Error:" in debug_result:
                    task = Task(description=f"Fix code: {code}", input_data=debug_result, agent_role="debugger")
                    code = self.agents["debugger"].run(task, self.memory)
                    code = code.strip().replace("", "").strip()
                    with open(script_path, "w") as f:
                        f.write(code)
                else:
                    break
        debug_result = debug_script(script_path, debug)
        return code, debug_result
