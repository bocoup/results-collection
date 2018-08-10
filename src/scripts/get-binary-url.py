#!/usr/bin/env python

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import contextlib
from datetime import datetime
import httplib
import json
import logging
import os
import re
import subprocess
import tempfile
import urlparse
import urllib


def main(browser_name, channel, application, os_name, bucket_name):
    '''Find the most recent build of a given browser or WebDriver server and
    provide a stable URL from which it may be downloaded. Because browser
    vendors do not necessarily commit to hosting outdated builds, this may
    involve downloading the build and persisting it to an internally-managed
    object storage location.'''

    log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
    logging.basicConfig(level='INFO', format=log_format)
    logger = logging.getLogger('get-browser-url')

    source_url = None

    logger.info(
      'Locating artifact for %s@%s %s', browser_name.title(), channel,
      application
    )

    if application == 'browser':
        product_id = browser_name

        if browser_name == 'firefox':
            source_url = locate_firefox(channel)
        elif browser_name == 'chrome':
            source_url = locate_chrome(channel)
    else:
        if channel != 'stable':
            raise ValueError(
                'Only stable versions of WebDriver binaries are available'
            )

        if browser_name == 'firefox':
            product_id = 'geckodriver'
            source_url = locate_geckodriver()
        elif browser_name == 'chrome':
            product_id = 'chromedriver'
            source_url = locate_chromedriver()

    if source_url is None:
        raise Exception('Unable to locate the requested artifact')

    logger.info('Artifact located at %s', source_url)

    directory = '%s-%s-%s' % (product_id, channel, os_name)
    identifier = get_identifier(source_url)
    uri = '%s/%s/%s' % (bucket_name, directory, identifier)

    url = get_mirrored(uri)

    if url is None:
        logger.info('Unable to find mirrored version. Mirroring...')

        mirror(source_url, uri)

        url = get_mirrored(uri)

    assert url is not None

    logger.info('Mirrored version found at %s', url)

    return url


def locate_firefox(channel):
    if channel == 'experimental':
        browser_name = 'firefox-nightly-latest-ssl'
    else:
        browser_name = 'firefox-latest-ssl'

    url = ('https://download.mozilla.org/?product=%s&os=linux64&lang=en-US' %
           browser_name)

    with request('HEAD', url) as response:
        return response.getheader('Location')


def locate_geckodriver():
    parts = urlparse.urlparse(
        'https://api.github.com/repos/mozilla/geckodriver/releases/latest'
    )
    conn = httplib.HTTPSConnection(parts.netloc)
    # > By default, all requests to https://api.github.com receive the v3
    # > version of the REST API. We encourage you to explicitly request this
    # > version via the Accept header.
    #
    # Source: https://developer.github.com/v3/
    headers={'User-Agent': 'wpt-results-collector', 'Accept': 'application/vnd.github.v3+json'}
    conn.request('GET', parts.path, headers=headers)

    data = json.loads(conn.getresponse().read())

    for asset in data['assets']:
        if 'linux64' in asset['name']:
            with request('HEAD', asset['browser_download_url']) as response:
                return response.getheader('Location')


def locate_chrome(channel):
    if channel == 'experimental':
        release_name = 'unstable_current'
    else:
        release_name = 'stable_current'

    return ('https://dl.google.com/linux/direct/google-chrome-%s_amd64.deb' %
            release_name)


def locate_chromedriver():
    parts = urlparse.urlparse(
        'https://chromedriver.storage.googleapis.com/LATEST_RELEASE'
    )
    conn = httplib.HTTPSConnection(parts.netloc)
    conn.request('GET', parts.path)
    latest_version = conn.getresponse().read()
    return 'https://chromedriver.storage.googleapis.com/%s/chromedriver_linux64.zip' % latest_version


@contextlib.contextmanager
def request(method, url):
    parts = urlparse.urlparse(url)
    if parts.scheme == 'https':
        Connection = httplib.HTTPSConnection
    else:
        Connection = httplib.HTTPConnection
    conn = Connection(parts.netloc)
    path = parts.path
    if parts.query:
        path += '?%s' % parts.query
    conn.request(method, path)

    yield conn.getresponse()

    conn.close()


def get_identifier(source_artifact_url):
    # A HEAD request would be more appropriate for this purpose, but some hosts
    # (e.g. GitHub.com's storage for releases) do not support that method.
    with request('GET', source_artifact_url) as response:
        etag = response.getheader('etag')
        return re.match('"?([^"]*)"?', etag).groups()[0]


def get_mirrored(uri):
    mirrored = 'https://storage.googleapis.com/%s' % uri
    with request('HEAD', mirrored) as response:
        if response.status >= 200 and response.status < 300:
            return mirrored


def mirror(source_artifact_url, uri):
    artifact_file = tempfile.mkstemp()[1]
    metadata_file = tempfile.mkstemp()[1]

    try:
        opener = urllib.URLopener()
        opener.retrieve(source_artifact_url, artifact_file)
        metadata = {
            'url': source_artifact_url,
            'date': str(datetime.utcnow()),
        }

        with open(metadata_file, 'w') as handle:
            json.dump(metadata, handle)

        subprocess.check_call([
            'gsutil', 'cp', artifact_file, 'gs://%s' % uri
        ])
        subprocess.check_call([
            'gsutil', 'cp', metadata_file, 'gs://%s.json' % uri
        ])
    finally:
        os.remove(artifact_file)
        os.remove(metadata_file)


parser = argparse.ArgumentParser(description=main.__doc__)
parser.add_argument('--browser_name',
                    choices=('firefox', 'chrome'),
                    required=True)
parser.add_argument('--channel',
                    choices=('stable', 'experimental'),
                    required=True)
parser.add_argument('--application',
                    choices=('browser', 'webdriver'),
                    required=True)
parser.add_argument('--os-name',
                    choices=('linux',),
                    required=True)
parser.add_argument('--bucket-name',
                    required=True)


if __name__ == '__main__':
    print main(**vars(parser.parse_args()))
