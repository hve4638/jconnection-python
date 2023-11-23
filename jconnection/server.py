import sys
import socket
import select
from threading import Thread
from typing import Callable
from .socketout import SocketOut, ClosedSocketOut
from .accumulatejsonparser import AccumulateJsonParser

class Server:
    def __init__(self, host="127.0.0.1", port=8080):
        self.sock:socket.socket = None
        self.host = host
        self.port = port
        self.recv_size = 4096
        self.clients = []

    def connect(self, recv_size = 4096,
                on_connected:Callable = lambda x : None,
                on_disconnected:Callable = lambda x : None,
                on_received:Callable = lambda x, y : None,
                on_error:Callable = lambda x, y : None,
            ):
        events = {
            "on_connected" : on_connected,
            "on_disconnected" : on_disconnected,
            "on_received" : on_received,
            "on_error" : on_error
        }
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)

        try:
            while True:
                sock, addr = self.sock.accept()
                self.__handle_client(sock, addr, events)
        except KeyboardInterrupt:
            sys.stdout.write("KeyboardInterrupt\n")
        finally:
            self.sock.close()
    
    def __handle_client(self, client_socket, addr, events):
        jparser = AccumulateJsonParser()
        sockout = SocketOut(client_socket, addr)
        events["on_connected"](sockout)
        try:
            while True:
                ready = select.select([client_socket], [], [], 1)
                if ready[0]:
                    data = client_socket.recv(self.recv_size)
                
                    if data:
                        jparser.update(data.decode())
                        
                        while jobj := jparser.parse():
                            try:
                                events["on_received"](sockout, jobj)
                            except Exception as ex:
                                events["on_error"](sockout, ex)
                    else:
                        # 연결이 끊긴경우
                        break
        finally:
            events["on_disconnected"](ClosedSocketOut(None, addr))
            client_socket.close()