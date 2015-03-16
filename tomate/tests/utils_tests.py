from __future__ import unicode_literals

import unittest


class FormatTimeLeftTestCase(unittest.TestCase):

    def test_format_time_left(self):
        from tomate.utils import format_time_left

        self.assertEqual('25:00', format_time_left(25 * 60))
        self.assertEqual('15:00', format_time_left(15 * 60))
        self.assertEqual('05:00', format_time_left(5 * 60))


class SupressErrorsDecoratorTestCase(unittest.TestCase):

    def test_suppress_errors(self):
        from tomate.utils import suppress_errors

        exception = Exception('error')

        @suppress_errors
        def raise_exception():
            raise exception

        self.assertEqual(None, raise_exception())
