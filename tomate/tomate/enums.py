from __future__ import unicode_literals

import enum


@enum.unique
class BaseEnum(enum.Enum):

    @classmethod
    def get_by_index(cls, index):
        for i, k in enumerate(cls):
            if i == index:
                return k


class Task(BaseEnum):
    pomodoro = 0
    shortbreak = 1
    longbreak = 2


class State(BaseEnum):
    stopped = 0
    running = 1


class Visible(BaseEnum):
    active = 0
    passive = 0
