from __future__ import unicode_literals

import locale
from locale import gettext as _

from gi.repository import Gtk
from wiring import inject, Module, SingletonScope

from tomate.signals import subscribe

locale.textdomain('tomate')


class Toolbar(Gtk.Toolbar):

    subscriptions = (
        ('session_ended', 'enable_start_button'),
        ('sessions_reseted', 'disable_reset_button'),
        ('session_started', 'enable_interrupt_button'),
        ('session_interrupted', 'enable_start_button'),
    )

    @subscribe
    @inject(session='tomate.session', appmenu='view.appmenu')
    def __init__(self, session, appmenu):
        self.appmenu = appmenu
        self.session = session

        Gtk.Toolbar.__init__(
            self,
            icon_size=Gtk.IconSize.LARGE_TOOLBAR,
            orientation=Gtk.Orientation.HORIZONTAL,
            toolbar_style=Gtk.ToolbarStyle.ICONS,
        )

        self.start_button = Gtk.ToolButton(stock_id='gtk-media-play',
                                           tooltip_text=_('Starts the session'))
        self.start_button.connect('clicked', self.on_start_button_clicked)
        self.insert(self.start_button, -1)

        self.interrupt_button = Gtk.ToolButton(stock_id='gtk-media-stop',
                                               tooltip_text=_('Interrupt the session'),
                                               visible=False,
                                               no_show_all=True)
        self.interrupt_button.connect('clicked', self.on_interrupt_button_clicked)
        self.insert(self.interrupt_button, -1)

        self.reset_button = Gtk.ToolButton(stock_id='gtk-refresh',
                                           sensitive=False,
                                           tooltip_text=_('Resets the count '
                                                          'of the pomodoros'))
        self.reset_button.connect('clicked', self.on_reset_button_clicked)
        self.insert(self.reset_button, -1)

        separator = Gtk.SeparatorToolItem(draw=False)
        separator.set_expand(True)
        self.insert(separator, -1)

        self.insert(self.appmenu, -1)

        style = self.get_style_context()
        style.add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)

    def on_start_button_clicked(self, widget):
        self.session.start()

    def on_interrupt_button_clicked(self, widget):
        self.session.interrupt()

    def on_reset_button_clicked(self, widget):
        self.session.reset()

    def enable_interrupt_button(self, sender=None, **kwargs):
        self.start_button.set_visible(False)

        self.interrupt_button.set_visible(True)

        self.reset_button.set_sensitive(False)

    def enable_start_button(self, sender=None, **kwargs):
        self.start_button.set_visible(True)

        self.interrupt_button.set_visible(False)

        sensitive = bool(kwargs.get('sessions'))
        self.reset_button.set_sensitive(sensitive)

    def disable_reset_button(self, sender=None, **kwargs):
        self.reset_button.set_sensitive(False)


class ToolbarProvider(Module):
    factories = {
        'view.toolbar': (Toolbar, SingletonScope)
    }
