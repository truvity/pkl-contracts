#!/usr/bin/env python3
"""Serves the release assets `just package` built in .out/ at the paths GitHub
serves them at, for hack/package-smoke.sh:

    /truvity/pkl-contracts/releases/download/v<version>/<name>@<version>[.zip|.sha256]

usage: serve-assets.py <.out dir> <file to write the port to> <seconds to live>
The server exits by itself after the given time.
"""
import http.server
import os
import re
import sys
import threading

root, port_file, ttl = sys.argv[1], sys.argv[2], float(sys.argv[3])


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        m = re.fullmatch(r"/truvity/pkl-contracts/releases/download/v[^/]+/((contracts\.[a-z]+@[0-9.]+)(\.zip|\.sha256|\.zip\.sha256)?)", self.path)
        path = os.path.join(root, m.group(2), m.group(1)) if m else None
        if path and os.path.isfile(path):
            body = open(path, "rb").read()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
with open(port_file, "w") as f:
    f.write(str(server.server_port))
threading.Timer(ttl, server.shutdown).start()
server.serve_forever()
