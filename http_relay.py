from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
from threading import Lock

messages = {}
lock = Lock()
MESSAGE_TTL = 60

class RelayHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logs

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body)
        
        with lock:
            target = data.get("to")
            if target:
                if target not in messages:
                    messages[target] = []
                messages[target].append({
                    "data": data,
                    "ts": time.time()
                })
                # Clean old messages
                messages[target] = [m for m in messages[target] if time.time() - m["ts"] < MESSAGE_TTL]
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def do_GET(self):
        target = self.path.split("/")[-1]
        
        with lock:
            if target in messages and messages[target]:
                msg = messages[target].pop(0)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(msg["data"]).encode())
            else:
                self.send_response(204)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), RelayHandler)
    print(f"[*] HTTP Relay running on port {port}")
    server.serve_forever()
