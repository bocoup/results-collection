from buildbot.plugins import steps
from buildbot.plugins import util

class SleepStep(steps.ShellCommand):
    def __init__(self, name, duration, *args, **kwargs):
        if name is None:
            name = 'Sleep'

        name += ' (%s seconds)' % duration

        kwargs['name'] = name
        kwargs['command'] = [
            'python', '-c', 'import time; time.sleep(%s)' % duration
        ]

        super(SleepStep, self).__init__(*args, **kwargs)
