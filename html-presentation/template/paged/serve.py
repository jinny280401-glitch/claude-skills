#!/usr/bin/env python3
"""本地预览：python3 serve.py [端口，默认 7350]，然后打开 http://localhost:7350/
服务本目录，关掉浏览器缓存（改了文件刷新就能看到）。"""
import http.server, os, sys, functools
port = int(sys.argv[1]) if len(sys.argv) > 1 else 7350
root = os.path.dirname(os.path.abspath(__file__))
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()
    def log_message(self, *a): pass
H.extensions_map.update({'.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.html': 'text/html; charset=utf-8'})
class S(http.server.ThreadingHTTPServer): daemon_threads = True
print('serving %s at http://localhost:%d/' % (root, port))
S(('127.0.0.1', port), functools.partial(H, directory=root)).serve_forever()
