from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

PORT = 8000
WEB_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(WEB_DIR)

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return

with HTTPServer(('0.0.0.0', PORT), Handler) as httpd:
    print(f'Serving webapp at http://localhost:{PORT}')
    print('Press Ctrl+C to stop')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped')
