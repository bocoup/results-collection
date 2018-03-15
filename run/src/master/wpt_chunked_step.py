from buildbot.plugins import steps

class WPTChunkedStep(steps.Trigger):
    def __init__(self, platform, total_chunks, *args, **kwargs):
        self.platform = platform
        self.total_chunks = total_chunks

        kwargs['name'] = str('Trigger %s chunks on %s' % (
            total_chunks, platform['browser_name'].title()
        ))

        super(WPTChunkedStep, self).__init__(*args, **kwargs)

    def getSchedulersAndProperties(self):
        spec = []

        for scheduler in self.schedulerNames:
            unimportant = scheduler in self.unimportantSchedulerNames

            for this_chunk in range(1, self.total_chunks + 1):
                spec.append({
                    'sched_name': scheduler,
                    'props_to_set': {
                        'this_chunk': this_chunk,
                        'total_chunks': self.total_chunks,
                        'browser_name': self.platform['browser_name'],
                        'browser_version': self.platform['browser_version'],
                        'os_name': self.platform['os_name'],
                        'os_version': self.platform['os_version'],
                        'use_sauce_labs': self.platform.get('sauce', False)
                    },
                    'unimportant': unimportant
                })

        return spec
