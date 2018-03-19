#!/usr/bin/env python

import argparse
import json
import logging
import requests


def main(browser_name, browser_version, os_name, os_version, wpt_revision,
         wptd_promote_url, results_summary_url):
    '''Thing'''
    wpt_commit_date = 'e'

    log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
    logging.basicConfig(level='INFO', format=log_format)
    logger = logging.getLogger('promote-results')

    logger.info('Creating new TestRun in the dashboard...')
    response = requests.post(wptd_promote_url,
        data=json.dumps({
            'browser_name': browser_name,
            'browser_version': browser_version,
            'commit_date': wpt_commit_date,
            'os_name': os_name,
            'os_version': os_version,
            'revision': wpt_revision,
            'results_url': results_summary_url
        }
    ))

    logger.info('Response status code: %s', response.status_code)
    logger.info('Response text: %s', response.text)

    assert response.status_code == 201


parser = argparse.ArgumentParser(description=main.__doc__)
parser.add_argument('--browser-name', required=True)
parser.add_argument('--browser-version', required=True)
parser.add_argument('--os-name', required=True)
parser.add_argument('--os-version', required=True)
parser.add_argument('--wpt-revision', required=True)
parser.add_argument('--wptd-upload-url', required=True)
parser.add_argument('--results-summary-url', required=True)

if __name__ == '__main__':
    main(**vars(parser.parse_args()))
