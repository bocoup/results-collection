from buildbot.plugins import steps

class WPTChunkedStep(steps.Trigger):
    def __init__(self, platform_manifest, total_chunks, *args, **kwargs):
        super(WPTChunkedStep, self).__init__(*args, **kwargs)
        self.platforms = []

        for platform_id in platform_manifest:
            platform_spec = platform_manifest[platform_id]

            if platform_spec['currently_run']:
                self.platforms.append(platform_spec)

        self.total_chunks = total_chunks

    def getSchedulersAndProperties(self):
        spec = []

        for scheduler in self.schedulerNames:
            unimportant = scheduler in self.unimportantSchedulerNames

            for platform in self.platforms:
                for this_chunk in range(1, self.total_chunks + 1):
                    spec.append({
                        'sched_name': scheduler,
                        'props_to_set': {
                            'this_chunk': this_chunk,
                            'total_chunks': self.total_chunks,
                            'browser_name': platform['browser_name'],
                            'browser_version': platform['browser_version'],
                            'os_name': platform['os_name'],
                            'os_version': platform['os_version']
                        },
                        'unimportant': unimportant
                    })

        return spec
