from __future__ import unicode_literals

import pytest

from tomate_gtk.utils import rounded_percent


@pytest.mark.parametrize('input, expected', [
    (1, 0),
    (8, 5),
    (10, 10),
    (11, 10),
    (14, 10),
    (15, 15),
    (16, 15),
])
def test_rounded_percent(input, expected):

    assert rounded_percent(input) == expected
