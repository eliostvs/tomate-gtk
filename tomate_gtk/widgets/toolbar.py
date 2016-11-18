from __future__ import unicode_literals

import locale
from locale import gettext as _

from gi.repository import Gtk
from tomate.constant import State
from tomate.event import Subscriber, Session, on
from wiring import inject
from wiring.scanning import register

locale.textdomain('tomate')


@register.factory('view.toolbar')
class Toolbar(Subscriber):
    @inject(session='tomate.session', appmenu='view.appmenu')
    def __init__(self, session, appmenu):
        self.session = session

        self.widget = Gtk.Toolbar(
            icon_size=Gtk.IconSize.LARGE_TOOLBAR,
            orientation=Gtk.Orientation.HORIZONTAL,
            toolbar_style=Gtk.ToolbarStyle.ICONS,
        )

        self.start_button = Gtk.ToolButton(stock_id='gtk-media-play',
                                           tooltip_text=_('Starts the session'))
        self.start_button.connect('clicked', self.on_start_button_clicked)
        self.widget.insert(self.start_button, -1)

        self.stop_button = Gtk.ToolButton(stock_id='gtk-media-stop',
                                          tooltip_text=_('Interrupt the session'),
                                          visible=False,
                                          no_show_all=True)
        self.stop_button.connect('clicked', self.on_stop_button_clicked)
        self.widget.insert(self.stop_button, -1)

        self.reset_button = Gtk.ToolButton(stock_id='gtk-refresh',
                                           sensitive=False,
                                           tooltip_text=_('Resets the count '
                                                          'of the pomodoros'))
        self.reset_button.connect('clicked', self.on_reset_button_clicked)
        self.widget.insert(self.reset_button, -1)

        separator = Gtk.SeparatorToolItem(draw=False)
        separator.set_expand(True)
        self.widget.insert(separator, -1)

        self.widget.insert(appmenu, -1)

        style = self.widget.get_style_context()
        style.add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)

    def on_start_button_clicked(self, widget):
        self.session.start()

    def on_stop_button_clicked(self, widget):
        self.session.stop()

    def on_reset_button_clicked(self, widget):
        self.session.reset()

    @on(Session, [State.started])
    def enable_stop_button(self, *args, **kwargs):
        self.start_button.set_visible(False)

        self.stop_button.set_visible(True)

        self.reset_button.set_sensitive(False)

    @on(Session, [State.stopped, State.finished])
    def enable_start_button(self, *args, **kwargs):
        self.start_button.set_visible(True)

        self.stop_button.set_visible(False)

        sensitive = bool(kwargs.get('sessions'))
        self.reset_button.set_sensitive(sensitive)

    @on(Session, [State.started, State.reset])
    def disable_reset_button(self, *args, **kwargs):
        self.reset_button.set_sensitive(False)
