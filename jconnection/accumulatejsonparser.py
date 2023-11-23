import json
from queue import Queue

class AccumulateJsonParser:
    def __init__(self):
        self.stored = ""
        self.count = 0
        self.results = Queue()
    
    def update(self, text):
        st = 0
        for pos, c in enumerate(text):
            if self.count:
                if c == "{": self.count += 1
                elif c == "}": self.count -= 1

                if not self.count:
                    self.results.put(self.stored + text[st:pos+1])
                    self.stored = ""
                    st = pos+1
            else:
                if c == "{":
                    self.count += 1
        self.stored = text[st:]

    def parse(self):
        if self.results.empty():
            return None
        else:
            return json.loads(self.results.get())
