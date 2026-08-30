import http.server, functools

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Expires", "0")
        super().end_headers()

http.server.ThreadingHTTPServer(
    ("0.0.0.0", 8323),
    functools.partial(NoCacheHandler, directory=os.getcwd() if (os:=__import__("os")) else ".")
).serve_forever()
