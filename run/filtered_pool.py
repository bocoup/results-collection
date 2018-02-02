# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import threading

class FilteredPool(object):
    def __init__(self, members=[]):
        self.items = []
        self.added = threading.Event()

        for member in members:
            self.add(member)

    def add(self, member):
        self.items.append(dict(lock=threading.Lock(), member=member))
        self.added.set()

    def match(self, *args):
        return True

    @contextlib.contextmanager
    def lease(self, *args):
        found = None

        while True:
            for item in self.items:
                if self.match(item['member'], *args) and item['lock'].acquire(False):
                    found = item
                    break

            if found:
                break

            self.added.clear()
            self.added.wait()

        try:
            yield found['member']
        finally:
            found['lock'].release()
            self.added.set()
