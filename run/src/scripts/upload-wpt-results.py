#!/usr/bin/env python

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import json
import gzip
import logging
import os
import requests
import shutil
import subprocess
import tempfile


def main(raw_results_directory, browser_name, browser_version, os_name,
         os_version, wpt_revision, wpt_revision_date, bucket_name, notify_url,
         notify_secret):
    '''Consolidate the data generated by the WPT CLI (via its `--log-wptreport`
    flag) into a set of gzip-encoded JSON files, upload those files to a Google
    Cloud Storage bucket, and send an HTTP request to a given web server to
    signal that this operation has occurred.'''

    log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
    logging.basicConfig(level='INFO', format=log_format)
    logger = logging.getLogger('upload-results')
    raw_results_files = [
        os.path.join(raw_results_directory, filename)
        for filename in os.listdir(raw_results_directory)
    ]

    summary = summarize(raw_results_files)

    temp_dir = tempfile.mkdtemp()

    try:
        summary_file_name = '%s-summary.json.gz' % browser_name

        logger.info('Writing %s to local filesystem', summary_file_name)

        write_gzip_json([temp_dir, summary_file_name], summary)

        full_results_dir = os.path.join(temp_dir, browser_name)

        logger.info('Writing %s results to local filesystem', len(summary))

        for test_filename, raw_result in each_result(raw_results_files):
            write_gzip_json([full_results_dir, test_filename], raw_result)

        upload_location = 'gs://%s/%s' % (bucket_name, wpt_revision)

        logger.info('Uploading results to %s', upload_location)

        upload(temp_dir, upload_location)

        logger.info('Upload successful.')

    finally:
        shutil.rmtree(temp_dir)

    logger.info('Notifying %s' % notify_url)

    status_code, response_text = notify(
        notify_url,
        notify_secret,
        {
            'browser_name': browser_name,
            'browser_version': browser_version,
            'os_name': os_name,
            'os_version': os_version,
            'revision': wpt_revision,
            'commit_date': wpt_revision_date,
            'results_url': '%s/%s' % (upload_location, summary_file_name)
        }
    )

    logger.info('Response status code: %s', status_code)
    logger.info('Response text: %s', response_text)

    assert status_code == 201


def each_result(raw_results_files):
    for filename in raw_results_files:
        with open(filename) as handle:
            contents = json.load(handle)

            assert 'results' in contents

            for result in contents['results']:
                assert 'test' in result

                # The "test" attribute describes the filesystem path to the
                # test file using a UNIX directory separator (`/`) and
                # including a leading separtor. Translate into a relative path
                # which is appropriate for the operating system executing this
                # script.
                test_filename_parts = result['test'].split('/')[1:]
                test_filename = os.path.sep.join(test_filename_parts)

                yield (test_filename, result)


def upload(dir_name, location):
    return_code = subprocess.check_call([
        'gsutil', '-m', '-h', 'Content-Encoding:gzip', 'rsync', '-r', dir_name,
        location
    ])

    assert return_code == 0


def write_gzip_json(filepath, payload):
    filename = os.path.sep.join(filepath)

    # Create all non-existent directories in a specified path
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError:
        pass

    with gzip.open(filename, 'wb') as f:
        payload_str = json.dumps(payload)
        f.write(payload_str)


def summarize(filenames):
    summary = {}

    for filename in filenames:
        with open(filename) as handle:
            data = json.load(handle)

        assert 'results' in data
        assert isinstance(data['results'], list)

        for result in data['results']:
            test_file = result['test']

            assert test_file not in summary, (
                'test_file "%s" is not already present in summary')

            assert 'status' in result

            if result['status'] in ('OK', 'PASS'):
                summary[test_file] = [1, 1]
            else:
                summary[test_file] = [0, 1]

            assert 'subtests' in result
            assert isinstance(result['subtests'], list)

            for subtest in result['subtests']:

                assert 'status'in subtest

                if subtest['status'] == 'PASS':
                    summary[test_file][0] += 1

                summary[test_file][1] += 1

    return summary


def notify(url, secret, payload):
    response = requests.post(url,
                             params={'secret': secret},
                             data=json.dumps(payload))

    return (response.status_code, response.text)


parser = argparse.ArgumentParser(description=main.__doc__)
parser.add_argument('--raw-results-directory', required=True)
parser.add_argument('--browser-name', required=True)
parser.add_argument('--browser-version', required=True)
parser.add_argument('--os-name', required=True)
parser.add_argument('--os-version', required=True)
parser.add_argument('--wpt-revision', required=True)
parser.add_argument('--wpt-revision-date', required=True)
parser.add_argument('--bucket-name', required=True)
parser.add_argument('--notify-url', required=True)
parser.add_argument('--notify-secret', required=True)

if __name__ == '__main__':
    main(**vars(parser.parse_args()))
