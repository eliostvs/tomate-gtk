from __future__ import unicode_literals

from wiring import implements, inject, Interface, Module, SingletonScope

from .enums import State, Task
from .signals import subscribe
from .utils import fsm


class ISession(Interface):

    state = ''
    duration = ''

    def start():
        pass

    def interrupt():
        pass

    def end():
        pass

    def change_task(task=None):
        pass

    def status():
        pass


@implements(ISession)
class Session(object):

    subscriptions = (
        ('timer_finished', 'on_timer_finished'),
    )

    @subscribe
    @inject(timer='tomate.timer', config='tomate.config', signals='tomate.signals')
    def __init__(self, timer, config, signals):
        super(Session, self).__init__()

        self.count = 0
        self.config = config
        self.state = State.stopped
        self.task = Task.pomodoro
        self.timer = timer
        self.signals = signals

    def timer_is_running(self):
        return self.timer.state == State.running

    def timer_is_not_running(self):
        return not self.timer_is_running()

    @fsm(target=State.running,
         source=[State.stopped],
         exit=lambda i: i.emit('session_started'))
    def start(self):
        self.timer.start(self.duration)

        return True

    @fsm(target=State.stopped,
         source=[State.running],
         conditions=[timer_is_running],
         exit=lambda i: i.emit('session_interrupted'))
    def interrupt(self):
        self.timer.stop()

        return True

    @fsm(target=State.stopped,
         source=[State.stopped],
         exit=lambda i: i.emit('sessions_reseted'))
    def reset(self):
        self.count = 0

        return True

    def on_timer_finished(self, *args, **kwargs):
        self.end()

    @fsm(target=State.stopped,
         source=[State.running],
         conditions=[timer_is_not_running],
         exit=lambda i: i.emit('session_ended'))
    def end(self):
        if self.task == Task.pomodoro:
            self.count += 1

            if self.count % self.config.get_int('Timer', 'Long Break Interval'):
                self.task = Task.shortbreak

            else:
                self.task = Task.longbreak

        else:
            self.task = Task.pomodoro

        return True

    @fsm(target=State.stopped,
         source=[State.stopped],
         exit=lambda i: i.emit('task_changed'))
    def change_task(self, task=None):
        if task is not None:
            self.task = task

        return True

    @property
    def duration(self):
        option_name = self.task.name + '_duration'
        minutes = self.config.get_int('Timer', option_name)
        return minutes * 60

    def status(self):
        return dict(task=self.task,
                    sessions=self.count,
                    state=self.state,
                    time_left=self.duration)

    def emit(self, signal):
        self.signals.emit(signal, **self.status())


class SessionProvider(Module):

    factories = {
        'tomate.session': (Session, SingletonScope)
    }
