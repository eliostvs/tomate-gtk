import logging

import wrapt

logger = logging.getLogger(__name__)


class fsm(object):
    def __init__(self, target, **kwargs):
        self.target = target
        self.source = kwargs.pop("source", "*")
        self.attr = kwargs.pop("attr", "state")
        self.conditions = kwargs.pop("conditions", [])
        self.exit_action = kwargs.pop("exit", None)

    def valid_transition(self, instance):
        if self.source == "*" or getattr(instance, self.attr) in self.source:
            return True

        return False

    def valid_conditions(self, instance):
        if not self.conditions:
            return True

        else:
            return all(map(lambda condition: condition(instance), self.conditions))

    def change_state(self, instance):
        current_target = getattr(instance, self.attr, None)

        logger.debug(
            "action=change instance=%s attr=%s from=%s to=%s",
            instance.__class__.__name__,
            self.attr,
            current_target,
            self.target,
        )

        if self.target != "self" and current_target != self.target:
            setattr(instance, self.attr, self.target)

    def call_exit_action(self, instance):
        if self.exit_action is not None:
            self.exit_action(instance)

    @wrapt.decorator
    def __call__(self, wrapped, instance, args, kwargs):
        logger.debug(
            "action=beforeCall instance=%s method=%s",
            instance.__class__.__name__,
            wrapped.__name__,
        )

        if self.valid_transition(instance) and self.valid_conditions(instance):
            result = wrapped(*args, **kwargs)

            self.change_state(instance)

            self.call_exit_action(instance)

            logger.debug(
                "action=call instance=%s method=%s result=true",
                instance.__class__.__name__,
                wrapped.__name__,
            )

            return result

        logger.debug(
            "action=call instance=%s method=%s result=false",
            instance.__class__.__name__,
            wrapped.__name__,
        )

        return False
