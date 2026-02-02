import logging

from gi.repository import Gio, Gtk
from wiring import Graph, SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import Bus, Events, Session, SessionType, Subscriber, on

from .shortcut import ShortcutEngine
from .systray import Systray
from .widgets import Countdown, HeaderBar, SessionButton

logger = logging.getLogger(__name__)


@register.factory("tomate.ui.view", scope=SingletonScope)
class Window(Subscriber):
    @inject(
        app="gtk.application",
        bus="tomate.bus",
        countdown="tomate.ui.countdown",
        graph=Graph,
        headerbar="tomate.ui.headerbar",
        about="tomate.ui.about",
        preference="tomate.ui.preference",
        session="tomate.session",
        session_button="tomate.ui.taskbutton",
        shortcuts="tomate.ui.shortcut",
    )
    def __init__(
        self,
        app: Gtk.Application,
        bus: Bus,
        countdown: Countdown,
        graph: Graph,
        headerbar: HeaderBar,
        about,
        preference,
        session: Session,
        session_button: SessionButton,
        shortcuts: ShortcutEngine,
    ):
        self._app = app
        self._session = session
        self._bus = bus
        self._graph = graph
        self._action_group = Gio.SimpleActionGroup()
        self.connect(bus)

        content = self._create_content(countdown, session_button)
        self.widget = self._create_window(headerbar, content)
        self.widget.insert_action_group("win", self._action_group)
        self._register_actions(session, about, preference)

        shortcuts.init(self.widget)
        session.ready()

    def _create_window(self, headerbar: HeaderBar, box: Gtk.Box) -> Gtk.Window:
        window = Gtk.ApplicationWindow(
            application=self._app,
            title="Tomate",
            resizable=False,
        )
        window.set_icon_name("tomate")
        window.set_default_size(350, -1)
        window.set_titlebar(headerbar.widget)
        window.connect("close-request", self.quit)
        window.set_child(box)
        return window

    def _create_content(self, countdown: Countdown, session_button: SessionButton) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.append(countdown.widget)
        box.append(session_button.widget)
        return box

    def run(self) -> None:
        logger.debug("action=run")
        self.widget.present()
        self._app.run()

    def _register_actions(self, session: Session, about, preference) -> None:
        self._add_action("show", lambda *_: self.show())
        self._add_action("hide", lambda *_: self.hide())
        self._add_action("preferences", lambda *_: preference.widget.present())
        self._add_action("about", lambda *_: about.widget.present())
        self._add_action("session-start", lambda *_: session.start())
        self._add_action("session-stop", lambda *_: session.stop())
        self._add_action("session-reset", lambda *_: session.reset())
        self._add_action("session-pomodoro", lambda *_: session.change(SessionType.POMODORO))
        self._add_action("session-short-break", lambda *_: session.change(SessionType.SHORT_BREAK))
        self._add_action("session-long-break", lambda *_: session.change(SessionType.LONG_BREAK))

    def _add_action(self, name: str, handler) -> None:
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", handler)
        self._action_group.add_action(action)

    def quit(self, *_) -> None:
        if self._session.is_running():
            return self.hide()
        else:
            logger.debug("action=quit")
            self._app.quit()

    def hide(self):
        self._bus.send(Events.WINDOW_HIDE)

        if Systray in self._graph.providers:
            logger.debug("action=hide strategy=tray")
            self.widget.hide()
            return True
        else:
            logger.debug("action=hide strategy=minimize")
            if hasattr(self.widget, "minimize"):
                self.widget.minimize()
            else:
                self.widget.set_visible(False)
            return True

    @on(Events.SESSION_END)
    def show(self, **__) -> None:
        logger.debug("action=show")
        self._bus.send(Events.WINDOW_SHOW)
        self.widget.present()
