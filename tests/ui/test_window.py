import pytest
from gi.repository import Gdk, Gtk

from tests.conftest import assert_received_event, deliver_events
from tomate.pomodoro import Bus, Config, Events, Graph, PluginEngine, Session
from tomate.ui import SysTray, SystrayMenu, Window
from tomate.ui.testing import Q, create_session_payload


@pytest.fixture
def systray() -> SysTray:
    return SysTray()


@pytest.fixture
def window(bus, config, plugin_engine, session, systray) -> Window:
    graph = Graph()
    graph.register_instance(Bus, bus)
    graph.register_instance(Config, config)
    graph.register_instance(Session, session)
    graph.register_instance(PluginEngine, plugin_engine)
    graph.register_instance(SysTray, systray)
    graph.register_factory(Window, Window)
    return graph.resolve(Window)


def test_init(session, window):
    session.ready.assert_called_once_with()

    # session button
    assert Q.select(window.widget, Q.props("name", "session.pomodoro"))
    assert Q.select(window.widget, Q.props("name", "session.short_break"))
    assert Q.select(window.widget, Q.props("name", "session.long_break"))

    # headerbar
    assert Q.select(window.widget, Q.props("name", "session.start"))
    assert Q.select(window.widget, Q.props("name", "session.reset"))
    assert Q.select(window.widget, Q.props("name", "session.stop"))

    # countdown
    assert Q.select(window.widget, Q.props("label", "00:00"))


def test_run(mocker, window):
    gtk_main = mocker.patch("tomate.ui.window.Gtk.main")
    show_all = mocker.patch("tomate.ui.window.Gtk.Window.show_all")

    window.run()

    gtk_main.assert_called_once_with()
    show_all.assert_called_once_with()


class TestWindowHide:
    def test_iconify_when_tray_icon_plugin_is_not_registered(self, window, bus, mocker):
        subscriber = mocker.Mock()
        bus.connect(Events.WINDOW_HIDE, subscriber)

        result = window.hide()

        assert result is Gtk.true
        subscriber.assert_not_called()
        deliver_events()
        assert_received_event(subscriber, Events.WINDOW_HIDE, None)

    def test_deletes_when_a_tray_system_is_active(self, bus, mocker, systray, window):
        systray.register(mocker.Mock())
        subscriber = mocker.Mock()
        bus.connect(Events.WINDOW_HIDE, subscriber)
        window.widget.set_visible(True)

        result = window.hide()

        assert result
        assert window.widget.get_visible() is False
        deliver_events()
        assert_received_event(subscriber, Events.WINDOW_HIDE, None)


class TestWindowQuit:
    def test_quits_when_timer_is_not_running(self, mocker, session, window):
        main_quit = mocker.patch("tomate.ui.window.Gtk.main_quit")
        session.is_running.return_value = False

        window.widget.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))

        main_quit.assert_called_once_with()

    def test_hides_when_timer_is_running(self, bus, mocker, session, window):
        session.is_running.return_value = True
        subscriber = mocker.Mock()
        bus.connect(Events.WINDOW_HIDE, subscriber)

        window.widget.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))

        deliver_events()
        assert_received_event(subscriber, Events.WINDOW_HIDE, None)


def test_shows_window_and_updates_systray_after_session_end(bus, mocker, window):
    systray_menu = SystrayMenu(bus, window)
    bus.publish(Events.WINDOW_HIDE)
    deliver_events()

    window.widget.props.visible = False
    subscriber = mocker.Mock()
    bus.connect(Events.WINDOW_SHOW, subscriber)

    payload = create_session_payload()
    bus.publish(Events.SESSION_END, payload=payload)

    assert window.widget.props.visible is False
    assert systray_menu.hide_item.props.visible is False
    assert systray_menu.show_item.props.visible is True
    deliver_events()

    assert window.widget.props.visible is True
    assert systray_menu.hide_item.props.visible is True
    assert systray_menu.show_item.props.visible is False
    assert_received_event(subscriber, Events.WINDOW_SHOW, None)
