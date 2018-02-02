import sys
import threading

from filtered_pool import FilteredPool

browsers = [
    {'name': 'firefox', 'version': '1'},
    {'name': 'chrome', 'version': '1'},
    {'name': 'safari', 'version': '1'},
    {'name': 'edge', 'version': '1'}
]
servers = [
    {'ip': 'fx1.workers.bocoup.com', 'browser_name': 'firefox'},
    {'ip': 'fx2.workers.bocoup.com', 'browser_name': 'firefox'},
    {'ip': 'fx3.workers.bocoup.com', 'browser_name': 'firefox'},
    {'ip': 'cr1.workers.bocoup.com', 'browser_name': 'chrome'},
    {'ip': 'cr2.workers.bocoup.com', 'browser_name': 'chrome'},
    {'ip': 'sf1.workers.bocoup.com', 'browser_name': 'safari'},
    {'ip': 'bocoup.browserstack.com', 'browser_name': 'safari'},
    {'ip': 'mse.workers.bocoup.com', 'browser_name': 'edge'},
]

jobs = [
    {'paths': ['css']},
    {'paths': ['dom']},
    {'paths': ['html']},
    {'paths': ['service-workers']}
]


class ServerPool(FilteredPool):
    def match(self, server, browser, job):
        return server['browser_name'] == browser['name']


server_pool = ServerPool(servers)
threads = []


def simulate_job(job):
    if 'css' in job['paths']:
        duration = 3
    elif 'service-workers' in job['paths']:
        duration = 1
    else:
        duration = 2

    import time
    time.sleep(duration)


def run_job(browser, job):
    with server_pool.lease(browser, job) as server:
        run_id = '%s\t%s\t%s' % (
            server['browser_name'], server['ip'], ':'.join(job['paths']))
        sys.stdout.write('start\t%s\n' % run_id)

        simulate_job(job)

        sys.stdout.write('finish\t%s\n' % run_id)


for browser in browsers:
    for job in jobs:
        thread = threading.Thread(target=run_job, args=(browser, job))
        thread.start()
        threads.append(thread)

for thread in threads:
    result = thread.join()
