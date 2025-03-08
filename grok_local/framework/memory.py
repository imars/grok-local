import os
import json

class Memory:
    def __init__(self, path="grok_local/memory"):
        self.path = path
        os.makedirs(path, exist_ok=True)
        self.file = os.path.join(path, "memory.json")
        if not os.path.exists(self.file):
            with open(self.file, "w") as f:
                json.dump([], f)

    def store(self, key, value):
        with open(self.file, "r") as f:
            data = json.load(f)
        data.append({"key": key, "value": value})
        with open(self.file, "w") as f:
            json.dump(data, f, indent=4)

    def retrieve(self, key):
        with open(self.file, "r") as f:
            data = json.load(f)
        for entry in data:
            if entry["key"] == key:
                return entry["value"]
        return None
