#!/usr/bin/env python3
"""A client for residentd.mjs that is not Node: length-prefixed JSON frames over a Unix socket or TCP.

    python3 client.py SOCKET_PATH|HOST:PORT TERMFILE [K] [C]     # K jobs at concurrency C; prints latency + host timing
    python3 client.py SOCKET_PATH|HOST:PORT --stats

Library use: ResidentClient(addr).reduce(term) -> the host's result dict (plus serverMs).
"""
import json, socket, struct, sys, threading, time, statistics as st


class ResidentClient:
    def __init__(self, addr, timeout=30.0):
        if ':' in addr and not addr.startswith('/'):
            host, port = addr.rsplit(':', 1)
            self.sock = socket.create_connection((host, int(port)), timeout=timeout)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        else:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            self.sock.connect(addr)
        self.next_id = 1

    def _send(self, obj):
        body = json.dumps(obj).encode('utf-8')
        self.sock.sendall(struct.pack('>I', len(body)) + body)

    def _recv(self):
        hdr = b''
        while len(hdr) < 4:
            chunk = self.sock.recv(4 - len(hdr))
            if not chunk:
                raise ConnectionError('closed')
            hdr += chunk
        n = struct.unpack('>I', hdr)[0]
        body = b''
        while len(body) < n:
            chunk = self.sock.recv(min(65536, n - len(body)))
            if not chunk:
                raise ConnectionError('closed')
            body += chunk
        return json.loads(body)

    def reduce(self, term):
        jid = self.next_id
        self.next_id += 1
        self._send({'id': jid, 'term': term})
        reply = self._recv()
        assert reply.get('id') == jid, reply
        return reply

    def cancel(self, jid):
        self._send({'id': jid, 'cancel': True})

    def stats(self):
        self._send({'op': 'stats'})
        return self._recv()

    def close(self):
        self.sock.close()


def main():
    addr, rest = sys.argv[1], sys.argv[2:]
    if rest and rest[0] == '--stats':
        print(json.dumps(ResidentClient(addr).stats(), indent=1))
        return
    term = open(rest[0], encoding='utf-8').read()
    K = int(rest[1]) if len(rest) > 1 else 100
    C = int(rest[2]) if len(rest) > 2 else 1
    lat, srv, run, inst, status = [], [], [], [], {}
    lock = threading.Lock()

    def worker(n):
        c = ResidentClient(addr)
        for _ in range(n):
            t0 = time.perf_counter()
            r = c.reduce(term)
            dt = (time.perf_counter() - t0) * 1000
            with lock:
                lat.append(dt); srv.append(r.get('serverMs', 0))
                t = r.get('timing') or {}
                run.append(t.get('run_ms', 0)); inst.append(t.get('instantiate_ms', 0))
                status[r.get('status')] = status.get(r.get('status'), 0) + 1
        c.close()

    worker(1); lat.clear(); srv.clear(); run.clear(); inst.clear(); status.clear()  # warm-up
    t0 = time.perf_counter()
    ths = [threading.Thread(target=worker, args=(K // C,)) for _ in range(C)]
    [t.start() for t in ths]; [t.join() for t in ths]
    wall = time.perf_counter() - t0
    q = lambda v, p: st.quantiles(v, n=100)[p - 1] if len(v) >= 100 else sorted(v)[min(len(v) - 1, int(len(v) * p / 100))]
    print(json.dumps(dict(addr=addr, term=rest[0].split('/')[-1], term_bytes=len(term.encode()), jobs=len(lat), concurrency=C, status=status,
                          client_ms_p50=round(st.median(lat), 3), client_ms_p99=round(q(lat, 99), 3), server_ms_p50=round(st.median(srv), 3),
                          host_run_ms_p50=round(st.median(run), 3), host_instantiate_ms_p50=round(st.median(inst), 3),
                          jobs_per_s=round(len(lat) / wall, 1))))


if __name__ == '__main__':
    main()
