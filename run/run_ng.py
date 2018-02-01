import threading

from server_pool import ServerPool

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

servers = ServerPool(servers)
threads = []

for browser in browsers:
    for job in jobs:
        def doit(browser, job):
            with servers.for_job(browser, job) as server:
                server.run_job(job)

        thread = threading.Thread(target=doit, args=(browser, job))
        thread.start()
        threads.append(thread)

for thread in threads:
    thread.join()
