from typing import List

class RequiresManualIntervention(Exception):
    def __init__(self, appids: List[int], name: str, message: str=""):
        self.appids = appids
        self.name = name
        self.message = message
        super().__init__(self.message)
