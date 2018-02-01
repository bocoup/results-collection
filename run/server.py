import sys
import threading

class Server(object):
    def __init__(self, attrs):
        self.attrs = attrs
        self.lock = threading.Lock()

    def can_run(self, browser, job):
        return self.attrs['browser_name'] == browser['name']

    def run_job(self, job):
        run_id = '%s\t%s\t%s' % (
            self.attrs['browser_name'], self.attrs['ip'], ':'.join(job['paths']))
        sys.stdout.write('start\t%s\n' % run_id)

        self.run_job_fake(job)

        sys.stdout.write('finish\t%s\n' % run_id)

    def run_job_fake(self, job):
        if 'css' in job['paths']:
            duration = 14
        elif 'service-workers' in job['paths']:
            duration = 3
        else:
            duration = 8

        import time
        time.sleep(duration)
