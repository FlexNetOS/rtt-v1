#!/usr/bin/env python3
import os, socket, json, pathlib, threading
ROOT = pathlib.Path(__file__).resolve().parents[1]
SOCK = ROOT/".rtt"/"sockets"/"agent-bus.sock"
try: os.unlink(SOCK)
except FileNotFoundError: pass
srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
srv.bind(str(SOCK)); srv.listen(16)
subs = {}
def client(conn):
    buf = b""; topic=None
    while True:
        data = conn.recv(4096)
        if not data: break
        buf += data
        try:
            msg = json.loads(buf.decode()); buf=b""
            op = msg.get("op")
            if op=="sub":
                topic = msg.get("topic","default")
                subs.setdefault(topic, []).append(conn)
                conn.send(b'{"ok":true}\n')
            elif op=="pub":
                t = msg.get("topic","default")
                for c in subs.get(t,[]): 
                    if c is not conn: c.send((json.dumps({"topic":t,"data":msg.get("data")})+"\n").encode())
                conn.send(b'{"ok":true}\n')
        except Exception: pass
    try:
        if topic and conn in subs.get(topic,[]): subs[topic].remove(conn)
    except: pass
    conn.close()
print("[OK] agent bus:", SOCK)
while True:
    c,_ = srv.accept()
    threading.Thread(target=client, args=(c,), daemon=True).start()
