import pytest
from gi.repository import Gtk
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui
from tomate.core import Sessions, State
from tomate.core.event import connect_events, Events, Session
from tomate.core.session import SessionPayload, FinishedSession
from tomate.ui.shortcut import ShortcutManager
from tomate.ui.widgets import HeaderBar, HeaderBarMenu

ONE_FINISHED_SESSION = [FinishedSession(1, Sessions.pomodoro, 10)]
NO_FINISHED_SESSIONS = []


@pytest.fixture
def mock_menu(mocker):
    return mocker.Mock(HeaderBarMenu, widget=Gtk.Menu())


def describe_headerbar():
    @pytest.fixture
    def subject(mock_session, mock_shortcuts, mock_menu):
        Session.receivers.clear()

        subject = HeaderBar(mock_session, mock_menu, mock_shortcuts)

        connect_events(subject)

        return subject

    def test_module(graph, mocker):
        specification = "tomate.ui.headerbar"
        package = "tomate.ui.widgets.headerbar"

        scan_to_graph([package], graph)

        assert specification in graph.providers

        graph.register_factory("tomate.ui.menu", mocker.Mock)
        graph.register_factory("tomate.session", mocker.Mock)
        graph.register_factory("tomate.ui.shortcut", mocker.Mock)
        graph.register_factory("tomate.ui.view", mocker.Mock)
        graph.register_factory("tomate.proxy", mocker.Mock)
        graph.register_factory("tomate.ui.about", mocker.Mock)
        graph.register_factory("tomate.ui.preference", mocker.Mock)

        provider = graph.providers[specification]
        assert provider.scope == SingletonScope

        assert isinstance(graph.get(specification), HeaderBar)

    def describe_buttons_behaviour():
        def test_connect_shortcuts(mock_shortcuts, subject):
            # start
            mock_shortcuts.connect.assert_any_call(
                ShortcutManager.START, subject._on_start_button_clicked
            )
            tooltip = "Starts the session (start)"
            assert subject._start_button.get_tooltip_text() == tooltip

            # stop
            mock_shortcuts.connect.assert_any_call(
                ShortcutManager.STOP, subject._on_stop_button_clicked
            )
            tooltip = "Stops the session (stop)"
            assert subject._stop_button.get_tooltip_text() == tooltip

            # reset
            mock_shortcuts.connect.assert_any_call(
                ShortcutManager.RESET, subject._on_reset_button_clicked
            )
            tooltip = "Clear the count of sessions (reset)"
            assert subject._reset_button.get_tooltip_text() == tooltip

        def test_start_then_session_when_start_button_is_clicked(subject, mock_session):
            subject._start_button.emit("clicked")

            refresh_gui(0)

            mock_session.start.assert_called_once_with()

        def test_stop_the_session_when_stop_button_is_clicked(subject, mock_session):
            subject._stop_button.emit("clicked")

            refresh_gui(0)

            mock_session.stop.assert_called_once_with()

        def test_reset_the_session_when_reset_button_is_clicked(
            subject, mock_session: Session
        ):
            subject._reset_button.emit("clicked")

            refresh_gui(0)

            mock_session.reset.assert_called_once_with()

    def describe_session_lifecycle():
        def test_enable_only_the_stop_button_when_session_starts(subject):
            # when
            Session.send(State.started)

            # then
            assert subject._stop_button.get_visible() is True
            assert subject._start_button.get_visible() is False
            assert subject._reset_button.get_sensitive() is False

        def test_disables_reset_button_when_session_is_reset(subject, mock_session):
            # given
            subject._reset_button.set_sensitive(True)

            # when
            Session.send(State.reset)

            # then
            assert subject._reset_button.get_sensitive() is False

        def test_buttons_visibility_and_title_in_the_first_session(
            subject, mock_session
        ):
            # given
            payload = SessionPayload(
                type=Sessions.pomodoro,
                sessions=NO_FINISHED_SESSIONS,
                state=State.started,
                duration=0,
                task="",
            )

            for state in [State.stopped, State.finished]:
                # when
                Session.send(state, payload=payload)

                # then
                assert subject._start_button.get_visible() is True
                assert subject._stop_button.get_visible() is False
                assert subject._reset_button.get_sensitive() is False

                assert subject.widget.props.title == "No session yet"

        def test_buttons_visibility_and_title_in_past_session(subject, mock_session):
            # when
            payload = SessionPayload(
                type=Sessions.pomodoro,
                sessions=ONE_FINISHED_SESSION,
                state=State.finished,
                duration=1,
                task="",
            )

            for state in [State.stopped, State.finished]:
                # when
                Session.send(state, payload=payload)

                # then
                assert subject._stop_button.get_visible() is False
                assert subject._start_button.get_visible() is True
                assert subject._reset_button.get_sensitive() is True

                assert subject.widget.props.title == "Session 1"


@pytest.fixture
def mock_preference(mocker):
    return mocker.Mock(widget=mocker.Mock(Gtk.Dialog))


@pytest.fixture()
def mock_about(mocker):
    return mocker.Mock(widget=mocker.Mock(Gtk.Dialog))


def describe_headerbar_menu():
    @pytest.fixture
    def subject(mock_proxy, mock_about, mock_preference, mock_view):
        Events.View.receivers.clear()

        return HeaderBarMenu(mock_about, mock_preference, mock_proxy)

    def test_open_preference_dialog_when_preference_item_is_clicked(
        subject, mock_view, mock_preference
    ):
        # given
        subject._preference_item.activate()

        # when
        refresh_gui()

        # then
        mock_preference.widget.run.assert_called_once_with()
        mock_preference.widget.set_transient_for.assert_called_once_with(
            mock_view.widget
        )

    def test_open_about_dialog_when_about_item_is_clicked(
        subject, mock_view, mock_about
    ):
        # given
        subject._about_item.activate()

        # when
        refresh_gui()

        # then
        mock_about.widget.set_transient_for.assert_called_once_with(mock_view.widget)
        mock_about.widget.run.assert_called_once_with()

    def test_module(graph, mocker):
        specification = "tomate.ui.headerbar.menu"
        package = "tomate.ui.widgets.headerbar"

        graph.register_factory("tomate.ui.view", mocker.Mock)
        graph.register_factory("tomate.proxy", mocker.Mock)
        graph.register_factory("tomate.ui.about", mocker.Mock)
        graph.register_factory("tomate.ui.preference", mocker.Mock)

        scan_to_graph([package], graph)

        assert specification in graph.providers

        provider = graph.providers[specification]

        assert provider.scope == SingletonScope

        assert isinstance(graph.get(specification), HeaderBarMenu)
