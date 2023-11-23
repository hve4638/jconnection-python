#!/usr/bin/env python3
import socket
import select
import json
import queue
from threading import Thread, Condition, Lock
from typing import Callable
from .socketout import SocketOut, ClosedSocketOut
from .accumulatejsonparser import AccumulateJsonParser

class Client:
    def __init__(self, host, port, recv_size = 1024):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host:str = host
        self.port:int = port
        self.recv_size:int = recv_size
        self.recv_timeout = 1
        self.recvlistener_timeout = 1
        self.recv_queue:queue.Queue = queue.Queue()
        self.recv_listener:list[Callable] = []
        self.recv_listener_cond = Condition()
        self.sig_addrecvlistener = True
        
        self.task_end = False
        self.tasks:list[Thread] = []

        self.sockout:SocketOut = None

    def __recv(self):
        jparser = AccumulateJsonParser()
        while not self.task_end:
            try:
                ready = select.select([self.sock], [], [], self.recv_timeout)
                if ready[0]:
                    data = self.sock.recv(self.recv_size)
                    jparser.update(data.decode())

                    if result := jparser.parse():
                        self.recv_queue.put(result)
            except OSError:
                # 연결이 종료된다면 OSError 발생
                pass

    def __recvlistener(self):
        while not self.task_end:
            try:
                with self.recv_listener_cond:
                    while not self.recv_listener:
                        self.recv_listener_cond.wait()

                    data = self.recv_queue.get(block=True, timeout=self.recvlistener_timeout)
                    
                    while self.sig_addrecvlistener:
                        self.recv_listener_cond.wait()
                    for listener in self.recv_listener:
                        listener(self.sockout, data)
            except queue.Empty:
                continue

    def add_recvlistener(self, listener:Callable[[SocketOut, dict],None]):
        self.sig_addrecvlistener = True
        with self.recv_listener_cond:
            self.recv_listener.append(listener)
            self.sig_addrecvlistener = False
            self.recv_listener_cond.notify_all()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, t, value, trackback):
        self.close()
    
    def open(self):
        addr = (self.host, self.port)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(addr)
        
        self.sockout = SocketOut(self.sock, addr)

        self.task_end = False
        thread_recv = Thread(target=self.__recv)
        thread_recvlistener = Thread(target=self.__recvlistener)
        thread_recv.start()
        thread_recvlistener.start()
        self.tasks.append(thread_recv)
        self.tasks.append(thread_recvlistener)

    def close(self):
        self.sock.close()

        self.task_end = True
        
        for task in self.tasks:
            task.join()

    def recv(self, timeout=None):
        if self.recv_listener:
            raise Exception("Listener가 설정되어 있으면 recv()를 사용할 수 없습니다")
        try:
            return self.recv_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def send(self, jobj):
        jsonified = json.dumps(jobj)

        self.sock.sendall(jsonified.encode('utf-8'))
