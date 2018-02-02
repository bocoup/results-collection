# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest
import threading

from filtered_pool import FilteredPool


class CustomError(Exception):
    pass


class LockStepThread(threading.Thread):
    '''Utility for explicitly managing control flow in threads.'''

    def __init__(self, target):
        super(LockStepThread, self).__init__()
        self.target = target
        self.e = threading.Event()
        self.exception = None

    def c(self):
        '''Toggle execution between this thread and the caller.'''
        self.e.set()
        self.e.clear()
        self.e.wait(5)

    def join(self):
        self.c = lambda: None
        self.e.set()
        super(LockStepThread, self).join()

    def run(self):
        self.target(self)

        self.e.set()
        self.e.clear()


class TestFilteredPool(unittest.TestCase):

    def test_allmatch_sync_level_0(self):
        pool = FilteredPool([0, 1, 2])

        with pool.lease() as item:
            self.assertEqual(item, 0)

        with pool.lease() as item:
            self.assertEqual(item, 0)

        with pool.lease() as item:
            self.assertEqual(item, 0)

    def test_allmatch_sync_level_1(self):
        pool = FilteredPool([0, 1, 2])

        with pool.lease() as item:
            self.assertEqual(item, 0)

            with pool.lease() as item:
                self.assertEqual(item, 1)

        with pool.lease() as item:
            self.assertEqual(item, 0)

    def test_allmatch_sync_level_2(self):
        pool = FilteredPool([0, 1, 2])

        with pool.lease() as item:
            self.assertEqual(item, 0)

            with pool.lease() as item:
                self.assertEqual(item, 1)

                with pool.lease() as item:
                    self.assertEqual(item, 2)

            with pool.lease() as item:
                self.assertEqual(item, 1)

        with pool.lease() as item:
            self.assertEqual(item, 0)

    def test_noitems_sync(self):
        pool = FilteredPool([])

        with self.assertRaises(Exception):
            with pool.lease():
                pass

    def test_nomatch_sync(self):
        class RejectAll(FilteredPool):
            def match(self, item):
                return False

        pool = RejectAll([0, 1, 2])

        with self.assertRaises(Exception):
            with pool.lease():
                pass

    def test_match_args(self):
        class MatchSpy(FilteredPool):
            def __init__(self, items):
                super(MatchSpy, self).__init__(items)

                self.clear()

            def clear(self):
                self.args = []
                self.call_count = 0

            def match(self, *args):
                self.call_count += 1
                self.args.append(args)

                return True

        pool = MatchSpy([0, 1, 2])

        with pool.lease():
            self.assertEquals(pool.call_count, 1)
            self.assertEquals(pool.args, [(0,)])

            pool.clear()

            with pool.lease():
                self.assertEquals(pool.call_count, 2)
                self.assertEquals(pool.args, [(0,), (1,)])

        pool.clear()

        with pool.lease('lease arg 1'):
            self.assertEquals(pool.call_count, 1)
            self.assertEquals(pool.args, [(0, 'lease arg 1')])

            pool.clear()

            with pool.lease('lease arg 2'):
                self.assertEquals(pool.call_count, 2)
                self.assertEquals(pool.args, [
                    (0, 'lease arg 2'), (1, 'lease arg 2')
                ])

        pool.clear()

        with pool.lease('first lease arg 1', 'second lease arg 1'):
            self.assertEquals(pool.call_count, 1)
            self.assertEquals(pool.args, [
                (0, 'first lease arg 1', 'second lease arg 1')
            ])

            pool.clear()

            with pool.lease('first lease arg 2', 'second lease arg 2'):
                self.assertEquals(pool.call_count, 2)
                self.assertEquals(pool.args, [
                    (0, 'first lease arg 2', 'second lease arg 2'),
                    (1, 'first lease arg 2', 'second lease arg 2')
                ])

    def test_match_raise(self):
        class MatchRaise(FilteredPool):
            def __init__(self, items):
                super(MatchRaise, self).__init__(items)

                self.should_raise = True

            def match(self, item):
                if self.should_raise:
                    raise CustomError()

                return True

        pool = MatchRaise([0, 1, 2])

        with self.assertRaises(CustomError):
            with pool.lease():
                pass

        pool.should_raise = False

        with pool.lease() as item:
            self.assertEqual(item, 0)

    def test_block_raise(self):
        err = Exception()
        pool = FilteredPool([0, 1, 2])

        with self.assertRaises(CustomError):
            with pool.lease() as item:
                self.assertEquals(item, 0)

                raise CustomError()

        with pool.lease() as item:
            self.assertEquals(
                item, 0, 'Previously-leased item is released despite exception'
            )

    def test_allmatch_async_first(self):
        pool = FilteredPool([0, 1, 2])
        active = []

        def get(self):
            self.c()

            with pool.lease() as item:
                active.append(item)
                self.c()

        threads = []

        for _ in [0, 0, 0, 0]:
            thread = LockStepThread(target=get)
            threads.append(thread)
            thread.start()

        self.assertEqual(active, [])

        threads[0].c()
        self.assertEqual(active, [0])

        threads[1].c()
        self.assertEqual(active, [0, 1])

        threads[2].c()
        self.assertEqual(active, [0, 1, 2])

        threads[0].c()
        threads[3].c()
        self.assertEqual(active, [0, 1, 2, 0])

        threads[1].join()
        threads[2].join()
        threads[3].join()

    def test_allmatch_async_second(self):
        pool = FilteredPool([0, 1, 2])
        active = []

        def get(self):
            self.c()

            with pool.lease() as item:
                active.append(item)
                self.c()

        threads = []

        for _ in [0, 0, 0, 0]:
            thread = LockStepThread(target=get)
            threads.append(thread)
            thread.start()

        self.assertEqual(active, [])

        threads[0].c()
        self.assertEqual(active, [0])

        threads[1].c()
        self.assertEqual(active, [0, 1])

        threads[2].c()
        self.assertEqual(active, [0, 1, 2])

        threads[1].c()
        threads[3].c()
        self.assertEqual(active, [0, 1, 2, 1])

        threads[0].join()
        threads[2].join()
        threads[3].join()

    def test_allmatch_async_third(self):
        pool = FilteredPool([0, 1, 2])
        active = []

        def get(self):
            self.c()

            with pool.lease() as item:
                active.append(item)
                self.c()

        threads = []

        for _ in [0, 0, 0, 0]:
            thread = LockStepThread(target=get)
            threads.append(thread)
            thread.start()

        self.assertEqual(active, [])

        threads[0].c()
        self.assertEqual(active, [0])

        threads[1].c()
        self.assertEqual(active, [0, 1])

        threads[2].c()
        self.assertEqual(active, [0, 1, 2])

        threads[2].c()
        threads[3].c()
        self.assertEqual(active, [0, 1, 2, 2])

        threads[0].join()
        threads[1].join()
        threads[3].join()


if __name__ == '__main__':
    unittest.main()
