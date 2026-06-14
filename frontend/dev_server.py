from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    server_address = ("", 5500)
    httpd = ThreadingHTTPServer(server_address, NoCacheHandler)

    print("Frontend running at http://127.0.0.1:5500")
    print("No-cache mode enabled for development.")
    httpd.serve_forever()