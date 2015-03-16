from __future__ import unicode_literals

import unittest
from tomate.enums import BaseEnum


class Dummy(BaseEnum):
    a = 1
    b = 2


class PomodoroTaskTestCase(unittest.TestCase):

    def test_get_task_by_index(self):
        self.assertEqual(Dummy.a, Dummy.get_by_index(0))
        self.assertEqual(Dummy.b, Dummy.get_by_index(1))
