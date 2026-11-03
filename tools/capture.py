#!/usr/bin/env python3
# Drive a running x64sc (-remotemonitor on 127.0.0.1:6510): wait for the
# intro SPACE loop at $3552, skip it by setting PC=$3559, then screenshot
# the waterfall twice (fli1.png, fli2.png) into the given directory and quit.
# Usage: tools/capture.py <outdir>   (see `make capture`)
import socket, time, sys
out = sys.argv[1]
def conn():
    for _ in range(50):
        try: return socket.create_connection(("127.0.0.1", 6510), timeout=3)
        except OSError: time.sleep(0.2)
    raise SystemExit("no monitor")
def cmd(s, c, wait=0.5):
    s.sendall((c+"\n").encode()); time.sleep(wait)
    data=b""
    s.settimeout(0.5)
    try:
        while True:
            d=s.recv(65536)
            if not d: break
            data+=d
    except socket.timeout: pass
    return data.decode(errors="replace")
time.sleep(6)            # let it unpack and reach the SPACE wait
s=conn()
print(cmd(s,"r"))
print(cmd(s,"d 3552 3559"))
print(cmd(s,"r pc = 3559"))
print(cmd(s,"x"))
s.close()
time.sleep(3)            # let the waterfall run
s=conn()
print(cmd(s,"r"))
print(cmd(s,f'screenshot "{out}/fli1.png" 2',1))
print(cmd(s,"x")); s.close()
time.sleep(0.7)
s=conn()
print(cmd(s,f'screenshot "{out}/fli2.png" 2',1))
print(cmd(s,"quit"))
