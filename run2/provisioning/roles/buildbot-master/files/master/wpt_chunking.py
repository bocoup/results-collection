from buildbot.plugins import steps
from buildbot.process import properties
from buildbot.schedulers import timed
from twisted.internet import defer

class ChunkScheduler(timed.Periodic):
    @defer.inlineCallbacks
    def startBuild(self):
        sourcestamps = [dict(codebase=cb) for cb in self.codebases]
        total = 5

        for this_chunk in range(1, total + 1):
            props = properties.Properties()
            props.setProperty('thisChunk', this_chunk, 'Scheduler')
            props.setProperty('totalChunks', total, 'Scheduler')

            yield self.addBuildsetForSourceStampsWithDefaults(
                properties=props,
                reason=self.reason,
                sourcestamps=sourcestamps)


class ChunkedCommand(steps.ShellCommand):
    def start(self):
        self.setCommand(
            'echo Chunk \#%s of %s && sleep 5 && echo Done' % (
                self.getProperty('thisChunk'), self.getProperty('totalChunks'))
        )

        return steps.ShellCommand.start(self)
