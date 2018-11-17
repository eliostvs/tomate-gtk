import locale
from locale import gettext as _

from gi.repository import Gtk
from tomate.constant import State
from tomate.event import Subscriber, Events, on
from wiring import inject, SingletonScope
from wiring.scanning import register


locale.textdomain("tomate")


@register.factory("view.headerbar", scope=SingletonScope)
class HeaderBar(Subscriber):
    @inject(session="tomate.session", menu="view.menu")
    def __init__(self, session, menu):
        self.session = session

        self.widget = Gtk.HeaderBar(
            show_close_button=True,
            title=_("No session yet"),
            decoration_layout=":close",
        )

        self.start_button = HeaderBar.button(
            Gtk.STOCK_MEDIA_PLAY, "Starts the session", self.on_start_button_clicked
        )

        self.widget.pack_start(self.start_button)

        self.stop_button = HeaderBar.button(
            Gtk.STOCK_MEDIA_STOP,
            "Stops the session",
            self.on_stop_button_clicked,
            visible=False,
            no_show_all=True,
        )

        self.widget.pack_start(self.stop_button)

        self.reset_button = HeaderBar.button(
            Gtk.STOCK_CLEAR,
            "Resets the current sessions",
            self.on_reset_button_clicked,
            sensitive=False,
        )
        self.widget.pack_start(self.reset_button)

        button = Gtk.MenuButton(popup=menu.widget)
        icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_PREFERENCES, Gtk.IconSize.BUTTON)
        button.add(icon)

        self.widget.pack_end(button)

    def on_start_button_clicked(self, widget):
        self.session.start()

    def on_stop_button_clicked(self, widget):
        self.session.stop()

    def on_reset_button_clicked(self, widget):
        self.session.reset()

    @on(Events.Session, [State.started])
    def on_session_started(self, *args, **kwargs):
        self.start_button.set_visible(False)

        self.stop_button.set_visible(True)

        self.reset_button.set_sensitive(False)

    @on(Events.Session, [State.stopped, State.finished])
    def on_session_stopped_or_finished(self, *args, **kwargs):
        self.start_button.set_visible(True)

        self.stop_button.set_visible(False)

        self.on_session_reset(**kwargs)

    @on(Events.Session, [State.reset])
    def on_session_reset(self, *args, **kwargs):
        sessions_count = kwargs.get("sessions")

        self.reset_button.set_sensitive(bool(sessions_count))

        self.widget.props.title = (
            _("Session {}".format(sessions_count))
            if sessions_count
            else _("No session yet")
        )

    @staticmethod
    def button(icon_name, tooltip_text, on_clicked, **props):
        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        image.show()

        button = Gtk.Button(tooltip_text=_(tooltip_text), **props)
        button.add(image)

        button.connect("clicked", on_clicked)

        return button
