"""Minimal Chrome DevTools Protocol client using only the standard library."""
import base64, json, os, socket, struct, subprocess, time, urllib.request

class CDP:
    def __init__(self, ws_url):
        host_port, path = ws_url[len('ws://'):].split('/', 1)
        host, port = host_port.split(':')
        self.sock = socket.create_connection((host, int(port)))
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f'GET /{path} HTTP/1.1\r\nHost: {host_port}\r\nUpgrade: websocket\r\n'
               f'Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n')
        self.sock.sendall(req.encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.sock.recv(4096)
        self.rest = buf.split(b'\r\n\r\n', 1)[1]
        self.id = 0
        self.events = []

    def _recv_exact(self, n):
        while len(self.rest) < n:
            chunk = self.sock.recv(1 << 20)
            if not chunk:
                raise EOFError
            self.rest += chunk
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def _recv_msg(self):
        data = b''
        while True:
            b1, b2 = self._recv_exact(2)
            fin, op = b1 & 0x80, b1 & 0x0f
            ln = b2 & 0x7f
            if ln == 126:
                ln = struct.unpack('>H', self._recv_exact(2))[0]
            elif ln == 127:
                ln = struct.unpack('>Q', self._recv_exact(8))[0]
            payload = self._recv_exact(ln)
            if op == 9:  # ping
                continue
            data += payload
            if fin:
                return json.loads(data.decode('utf-8', 'replace'))

    def _send(self, obj):
        data = json.dumps(obj).encode()
        hdr = bytearray([0x81])
        n = len(data)
        if n < 126:
            hdr.append(0x80 | n)
        elif n < 65536:
            hdr.append(0x80 | 126); hdr += struct.pack('>H', n)
        else:
            hdr.append(0x80 | 127); hdr += struct.pack('>Q', n)
        mask = os.urandom(4)
        hdr += mask
        self.sock.sendall(bytes(hdr) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def call(self, method, **params):
        self.id += 1
        mid = self.id
        self._send({'id': mid, 'method': method, 'params': params})
        while True:
            msg = self._recv_msg()
            if msg.get('id') == mid:
                if 'error' in msg:
                    raise RuntimeError(msg['error'])
                return msg.get('result', {})
            if 'method' in msg:
                self.events.append(msg)

    def js(self, expr, await_promise=True):
        r = self.call('Runtime.evaluate', expression=expr, returnByValue=True,
                      awaitPromise=await_promise, userGesture=True)
        if 'exceptionDetails' in r:
            d = r['exceptionDetails']
            return {'__error__': (d.get('exception') or {}).get('description') or d.get('text')}
        return r.get('result', {}).get('value')

    def pump(self, secs=0.3):
        self.sock.settimeout(secs)
        end = time.time() + secs
        try:
            while time.time() < end:
                self.events.append(self._recv_msg())
        except (socket.timeout, TimeoutError):
            pass
        finally:
            self.sock.settimeout(None)

    def errors(self, clear=True):
        out = []
        for e in self.events:
            m = e.get('method')
            if m == 'Runtime.exceptionThrown':
                d = e['params']['exceptionDetails']
                out.append('EXC: ' + ((d.get('exception') or {}).get('description') or d.get('text', ''))[:400])
            elif m == 'Runtime.consoleAPICalled' and e['params']['type'] in ('error', 'assert'):
                out.append('CONSOLE: ' + ' '.join(str(a.get('value', a.get('description', ''))) for a in e['params']['args'])[:400])
            elif m == 'Log.entryAdded' and e['params']['entry']['level'] == 'error':
                out.append('LOG: ' + e['params']['entry']['text'][:300] + ' ' + e['params']['entry'].get('url', '')[:120])
        if clear:
            self.events = []
        return out


def launch(url, port=9333, profile=None):
    profile = profile or os.path.join(os.path.dirname(__file__), 'chrome-profile')
    proc = subprocess.Popen(['chromium', '--headless=new', f'--remote-debugging-port={port}',
                             f'--user-data-dir={profile}', '--no-first-run', '--no-default-browser-check',
                             '--window-size=1366,900', 'about:blank'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
            page = next(t for t in tabs if t['type'] == 'page')
            break
        except Exception:
            time.sleep(0.2)
    c = CDP(page['webSocketDebuggerUrl'])
    c.call('Runtime.enable'); c.call('Log.enable'); c.call('Page.enable')
    c.call('Page.navigate', url=url)
    time.sleep(3)
    c.pump(0.5)
    return proc, c
