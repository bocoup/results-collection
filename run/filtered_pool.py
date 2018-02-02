# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import threading

class FilteredPool(object):
    '''Maintain a set of values that may be "leased" by exactly one thread of
    execution at any time. This differs from a traditional thread-save queue in
    that the leased value is selected according to some filtering criteria (see
    the `match` method).'''

    def __init__(self, members=[]):

        self.items = []
        self.added = threading.Event()

        for member in members:
            self.add(member)

    def add(self, member):
        self.items.append(dict(lock=threading.Lock(), member=member))
        self.added.set()

    def match(self, *args):
        '''Determine if a value is suitable for leasing. The first argument to
        this method is the value being considered. All further positional
        arguments are forwarded from the invocation of `lease`.

        The default implementation leases any element unconditionally. It is
        intended to be over-ridden by inheriting classes (if not, a traditional
        thread-safe queue may be more appropriate).'''

        return True

    @contextlib.contextmanager
    def lease(self, *args):
        '''Retrieve an unclaimed value that satisfies some filtering criteria
        (see the `match` method) and ensure that no other threads receive this
        value until the value is released.'''

        has_candidate = False
        found = None

        while True:
            for item in self.items:
                if self.match(item['member'], *args):
                    has_candidate = True

                    if item['lock'].acquire(False):
                        found = item
                        break

            if found:
                break

            if not has_candidate:
                raise Exception(
                    'Pool contains no candidates which satisfy the provided ' +
                    '(locked or otherwise)'
                )

            self.added.clear()
            self.added.wait()

        try:
            yield found['member']
        finally:
            found['lock'].release()
            self.added.set()
