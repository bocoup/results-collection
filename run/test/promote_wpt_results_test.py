import BaseHTTPServer
import os
import subprocess
import threading
import unittest

here = os.path.dirname(os.path.abspath(__file__))
promote_bin = os.path.join(here, '../src/scripts/promote-wpt-results.py')

def target(server):
    server.serve_forever()


class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
        self.server.requests.append(self)
        self.send_response(self.server.status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()


class TestPromoteWptResults(unittest.TestCase):
    def setUp(self):
        self.server = None

    def tearDown(self):
        if self.server:
            self.server.shutdown()

    def start_server(self, port):
        self.server = BaseHTTPServer.HTTPServer(('', port), Handler)
        self.server.status_code = 200
        self.server.requests = []

        thread = threading.Thread(target=target, args=(self.server,))

        thread.start()

    def promote(self, browser_name, browser_version, os_name, os_version,
                wpt_revision, wptd_upload_url):
        proc = subprocess.Popen([
            promote_bin, '--browser-name', browser_name, '--browser-version',
            browser_version, '--os-name', os_name, '--os-version', os_version,
            '--wpt-revision', wpt_revision, '--wptd-upload-url', wptd_upload_url
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = proc.communicate()

        return (proc.returncode, stdout, stderr)

    def test_thing(self):
        self.start_server(8002)

        returncode, stdout, stderr = self.promote(
            'firefox', '4', 'linux64', '4', 'deadbeef', 'http://localhost:8002'
        )
        self.assertEqual(returncode, 0, stderr)

if __name__ == '__main__':
    unittest.main()
