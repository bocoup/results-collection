from buildbot.plugins import steps
from buildbot.plugins import util

class ThrottleStep(steps.ShellCommand):
    '''Pause build execution for the number of seconds specified by `duration`.
    This step is intended to be used when multiple builds execute in parallel
    and some shared resource should only be accessed at most one time in a
    given time period.

    - duration - amount of time (in seconds) that each build should wait
    - propertyName - the name of a Buildbot property which renders to a boolean
                     value describing if the current build should be throttled
    - lock - a Buildbot Interlock to use for synchronization
    '''

    def __init__(self, duration, propertyName, lock, *args, **kwargs):
        self.propertyName = propertyName
        self.lock = lock

        @util.renderer
        def locks(properties):
            if self.satisfiesCondition():
                return [self.lock.access('exclusive')]

            return []

        kwargs['locks'] = locks
        kwargs['doStepIf'] = lambda step: self.satisfiesCondition()
        # This command implements a platform-agnostic verison of the UNIX
        # `sleep` utility.
        kwargs['command'] = [
            'python', '-c', 'import time; time.sleep(%s)' % duration
        ]

        super(ThrottleStep, self).__init__(*args, **kwargs)

    def satisfiesCondition(self):
        return self.build.properties.getProperty(self.propertyName) == True
