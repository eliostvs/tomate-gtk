from __future__ import unicode_literals

from tomate.application import Application
from tomate.mixins import ConnectSignalMixin
from tomate.services import Cache


class GtkApplication(ConnectSignalMixin,
                     Application):

    signals = (
        ('setting_changed', 'on_setting_changed'),
    )

    def __init__(self, *args, **kwargs):
        super(GtkApplication, self).__init__(*args, **kwargs)

        Cache['GtkApplication'] = self

        self.connect_signals()

    def on_setting_changed(self, *args, **kwargs):
        section = kwargs.get('section')

        if section == 'Timer':
            self.change_task(self.pomodoro.task)
