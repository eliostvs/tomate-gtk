from __future__ import unicode_literals

import logging

import wrapt

logger = logging.getLogger(__name__)


def format_time_left(seconds):
    minutes, seconds = divmod(seconds, 60)
    return '{0:0>2}:{1:0>2}'.format(minutes, seconds)


@wrapt.decorator
def suppress_errors(wrapped, instance, args, kwargs):
    try:
        return wrapped(*args, **kwargs)

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(e, exc_info=True)

    return None


class fsm(object):

    def __init__(self, target, **kwargs):
        self.target = target
        self.source = kwargs.pop('source', '*')
        self.attr = kwargs.pop('attr', 'state')
        self.conditions = kwargs.pop('conditions', [])
        self.exit_action = kwargs.pop('exit', None)

    def valid_transition(self, instance):
        if self.source == '*' or getattr(instance, self.attr) in self.source:
            return True

    def valid_conditions(self, instance):
        if not self.conditions:
            return True

        else:
            return all(map(lambda condition: condition(instance), self.conditions))

    def change_state(self, instance):
        setattr(instance, self.attr, self.target)

    def call_exit_action(self, instance):
        if self.exit_action is not None:
            self.exit_action(instance)

    @wrapt.decorator
    def __call__(self, wrapped, instance, args, kwargs):
        if self.valid_transition(instance) and self.valid_conditions(instance):
            result = wrapped(*args, **kwargs)

            self.change_state(instance)

            self.call_exit_action(instance)

            return result

        return None
