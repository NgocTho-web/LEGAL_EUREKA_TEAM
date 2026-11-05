class Process:
    sequential = "sequential"
    hierarchical = "hierarchical"


class Agent:
    def __init__(self, *args, **kwargs):
        self.role = kwargs.get("role", "")
        self.goal = kwargs.get("goal", "")
        self.backstory = kwargs.get("backstory", "")
        self.tools = kwargs.get("tools", [])
        self.verbose = kwargs.get("verbose", False)
        self.allow_delegation = kwargs.get("allow_delegation", False)
        self.llm = kwargs.get("llm")


class Task:
    def __init__(self, *args, **kwargs):
        self.description = kwargs.get("description", "")
        self.expected_output = kwargs.get("expected_output", "")
        self.agent = kwargs.get("agent")
        self.context = kwargs.get("context", [])
        self.async_execution = kwargs.get("async_execution", False)


class Crew:
    def __init__(self, *args, **kwargs):
        self.agents = kwargs.get("agents", [])
        self.tasks = kwargs.get("tasks", [])
        self.process = kwargs.get("process")
        self.verbose = kwargs.get("verbose", False)

    def kickoff(self):
        return "Crew execution stub"


__all__ = ["Agent", "Task", "Crew", "Process"]
