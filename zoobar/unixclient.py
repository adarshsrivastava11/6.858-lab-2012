#!/usr/bin/python

import socket

def call(pn, req):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(pn)
    sock.send(req)
    sock.shutdown(socket.SHUT_WR)
    data = ""
    while True:
        buf = sock.recv(1024)
        if not buf:
            break
        data += buf
    sock.close()
    return data
