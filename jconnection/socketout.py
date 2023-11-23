import json

class SocketOut:
    def __init__(self, socket, addr=None):
        self.sock = socket
        self.__addr = addr
    
    def __str__(self):
        return f"<Socket({self.__addr})>"
    
    def send(self, jobj):
        jstr = json.dumps(jobj)
        self.sock.sendall(jstr.encode())

    def write(self, message):
        jobj = {
            "type" : "message",
            "message" : f"{message}",
        }
        jstr = json.dumps(jobj)
        self.sock.sendall(jstr.encode())
    
    def writeend(self):
        jobj = {
            "type" : "endofmessage",
        }
        jstr = json.dumps(jobj)
        self.sock.sendall(jstr.encode())

    def flush(self):
        pass

    @property
    def addr(self):
        return self.__addr

class ClosedSocketOut(SocketOut):
    def __init__(self, socket, addr):
        self.__addr = addr
    
    def __str__(self):
        return f"<Socket({self.__addr}) Closed>"
    
    def write(self, message):
        pass

    def writeend(self):
        pass

    def flush(self):
        pass

    @property
    def addr(self):
        return self.__addr