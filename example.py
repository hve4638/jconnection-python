#!/usr/bin/env python3
from threading import Thread
from time import sleep
import jconnection

host = "0.0.0.0"
port = 10000

def run_server():
    def on_recv(jsock:jconnection.SocketOut, data:dict):
        print("[Server] recv", data)
        jsock.send({"echo": data})
    
    server = jconnection.Server(host=host, port=port)
    server.connect(
        on_connected = lambda jsock : print("[Server] Connnected", jsock),
        on_disconnected = lambda jsock : print("[Server] Disconnected", jsock),
        on_received = on_recv,
        on_error=lambda jsock, ex : print("[Server] Error", ex)
    )

def run_client():
    def recv(jsock:jconnection.SocketOut, data:dict):
        print("[Client]", data)

    with jconnection.Client(host=host, port=port) as c:
        c.add_recvlistener(recv)
        c.send({"message": "hello"})
        sleep(1)


if __name__ == "__main__":
    Thread(target=run_client).start()

    run_server()