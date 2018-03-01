from buildbot.plugins import steps

class WPTChunkedStep(steps.Trigger):
    def __init__(self, browsers, total_chunks, *args, **kwargs):
        super(WPTChunkedStep, self).__init__(*args, **kwargs)
        self.browsers = browsers
        self.total_chunks = total_chunks

    def getSchedulersAndProperties(self):
        spec = []

        for scheduler in self.schedulerNames:
            unimportant = scheduler in self.unimportantSchedulerNames

            for browser in self.browsers:
                for this_chunk in range(1, self.total_chunks + 1):
                    spec.append({
                        'sched_name': scheduler,
                        'props_to_set': {
                            'this_chunk': this_chunk,
                            'total_chunks': self.total_chunks,
                            'browser': browser
                        },
                        'unimportant': unimportant
                    })

        return spec
