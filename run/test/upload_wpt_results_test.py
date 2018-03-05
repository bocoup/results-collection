import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

here = os.path.dirname(os.path.abspath(__file__))
gsutil_stub_dir = os.path.sep.join([here, 'gsutil-stub'])
gsutil_stub_args = os.path.sep.join([gsutil_stub_dir, 'gsutil_args.json'])
gsutil_stub_content = os.path.sep.join([gsutil_stub_dir, 'content-to-upload'])
upload_bin = os.path.sep.join(
    [here, '..', 'src', 'scripts', 'upload-wpt-results.py']
)

def make_results():
    return {
        '1_of_2.json': {
            'results': [
                {
                    'test': '/js/bitwise-or.html',
                    'status': 'OK',
                    'subtests': []
                },
                {
                    'test': '/js/bitwise-and.html',
                    'status': 'OK',
                    'subtests': [
                        {'status': 'FAIL', 'message': 'bad', 'name': 'first'},
                        {'status': 'FAIL', 'message': 'bad', 'name': 'second'}
                    ]
                }
            ]
        },
        '2_of_2.json': {
            'results': [
                {
                    'test': '/js/bitwise-or-2.html',
                    'status': 'OK',
                    'subtests': []
                }
            ]
        }
    }

class TestUploadWptResults(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        # gsutil "stub" output files and directories will only be present if
        # the tests were run previously
        try:
            os.remove(gsutil_stub_args)
        except OSError:
            pass

        try:
            shutil.rmtree(gsutil_stub_content)
        except OSError:
            pass

    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir)
        except OSError:
            pass

    def upload(self, browser_name, results_dir, results,
               gsutil_return_code = 0):
        env = dict(os.environ)
        env['PATH'] = gsutil_stub_dir + os.pathsep + os.environ['PATH']
        env['GSUTIL_RETURN_CODE'] = str(gsutil_return_code)

        for filename in results:
            with open(os.path.join(results_dir, filename), 'w') as handle:
                json.dump(results[filename], handle)

        proc = subprocess.Popen([
            upload_bin, '--raw-results-directory', results_dir,
            '--browser-name', browser_name, '--wpt-revision', '123456',
            '--bucket-name', 'wpt-test'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = proc.communicate()

        return (proc.returncode, stdout, stderr)

    def assertJsonFiles(self, dir_name, data):
        for filename in data:
            path = os.path.sep.join([dir_name] + filename.split('/'))

            with gzip.open(path) as handle:
                self.assertEqual(data[filename], json.loads(handle.read()))

    def test_basic_firefox(self):
        returncode, stdout, stderr = self.upload('firefox',
                                                 self.temp_dir,
                                                 make_results())

        self.assertEqual(returncode, 0, stderr)

        self.assertJsonFiles(gsutil_stub_content, {
            'firefox-summary.json.gz': {
                '/js/bitwise-and.html': [1, 3],
                '/js/bitwise-or-2.html': [1, 1],
                '/js/bitwise-or.html': [1, 1]
            },
            'firefox/js/bitwise-and.html': {
                'test': '/js/bitwise-and.html',
                'status': 'OK',
                'subtests': [
                    {u'message': 'bad', 'name': 'first', 'status': 'FAIL'},
                    {u'message': 'bad', 'name': 'second', 'status': 'FAIL'}
                ]
            },
            'firefox/js/bitwise-or.html': {
                'test': '/js/bitwise-or.html',
                'status': 'OK',
                'subtests': []
            },
            'firefox/js/bitwise-or-2.html':  {
                'test': '/js/bitwise-or-2.html',
                'status': u'OK',
                'subtests': []
            }
        })

    def test_basic_chrome(self):
        returncode, stdout, stderr = self.upload('chrome',
                                                 self.temp_dir,
                                                 make_results())

        self.assertEqual(returncode, 0, stderr)

        self.assertJsonFiles(gsutil_stub_content, {
            'chrome-summary.json.gz': {
                '/js/bitwise-and.html': [1, 3],
                '/js/bitwise-or-2.html': [1, 1],
                '/js/bitwise-or.html': [1, 1]
            },
            'chrome/js/bitwise-and.html': {
                'test': '/js/bitwise-and.html',
                'status': 'OK',
                'subtests': [
                    {u'message': 'bad', 'name': 'first', 'status': 'FAIL'},
                    {u'message': 'bad', 'name': 'second', 'status': 'FAIL'}
                ]
            },
            'chrome/js/bitwise-or.html': {
                'test': '/js/bitwise-or.html',
                'status': 'OK',
                'subtests': []
            },
            'chrome/js/bitwise-or-2.html':  {
                'test': '/js/bitwise-or-2.html',
                'status': u'OK',
                'subtests': []
            }
        })

    def test_failed_gsutil(self):
        returncode, stdout, stderr = self.upload('chrome',
                                                 self.temp_dir,
                                                 make_results(),
                                                 gsutil_return_code = 1)

        self.assertEqual(returncode, 1, stdout)

    def test_duplicated_results(self):
        duplicated_results = make_results()
        duplicated_results['2_of_2.json']['results'].append(
            duplicated_results['1_of_2.json']['results'][0]
        )
        returncode, stdout, stderr = self.upload('firefox',
                                                 self.temp_dir,
                                                 duplicated_results)

        self.assertEqual(returncode, 1, stdout)
        self.assertFalse(os.access(gsutil_stub_content, os.R_OK))


if __name__ == '__main__':
    unittest.main()
