import dbus
import pytest
from dbus.mainloop.glib import DBusGMainLoop
from dbusmock import DBusTestCase
from wiring.scanning import scan_to_graph

from tomate.pomodoro import State
from tomate.pomodoro.app import Application

DBusGMainLoop(set_as_default=True)


@pytest.fixture()
def mock_plugin(mocker):
    from yapsy.PluginManager import PluginManager

    return mocker.Mock(PluginManager)


@pytest.fixture()
def subject(graph, mock_view, mock_plugin, mocker):
    graph.register_instance("tomate.ui.view", mock_view)
    graph.register_instance("tomate.plugin", mock_plugin)
    graph.register_instance("dbus.session", mocker.Mock())

    scan_to_graph(["tomate.pomodoro.app"], graph)

    return graph.get("tomate.app")


def test_module(graph, subject):
    instance = graph.get("tomate.app")

    assert isinstance(instance, Application)
    assert instance is subject


def test_search_plugin_on_init(subject, mock_plugin):
    mock_plugin.collectPlugins.assert_called_once()


class TestRun:
    def test_shows_window_when_app_is_running(self, subject):
        subject.state = State.stopped

        subject.Run()

        subject.window.run.assert_called_once_with()

    def test_runs_window_when_app_is_not_running(self, subject):
        subject.state = State.started

        subject.Run()

        subject.window.show.assert_called_once_with()
        assert subject.state is State.started


class TestFromGraph:
    def setup_method(self):
        DBusTestCase.start_session_bus()

    def teardown_method(self):
        DBusTestCase.tearDownClass()

    def test_create_app_instance_when_is_not_registered_in_dbus(
        self, graph, mock_view, mock_plugin
    ):
        graph.register_instance("tomate.ui.view", mock_view)
        graph.register_instance("tomate.plugin", mock_plugin)
        scan_to_graph(["tomate.pomodoro.app"], graph)

        instance = Application.from_graph(graph, DBusTestCase.get_dbus())

        assert isinstance(instance, Application)

    @pytest.fixture()
    def mock_dbus(self):
        mock = DBusTestCase.spawn_server(
            Application.BUS_NAME, Application.BUS_PATH, Application.BUS_INTERFACE
        )
        yield mock
        mock.terminate()
        mock.wait()

    def test_get_dbus_interface_when_is_registered_in_dbus(self, graph, mock_dbus):
        instance = Application.from_graph(graph, DBusTestCase.get_dbus())

        assert isinstance(instance, dbus.Interface)
        assert instance.dbus_interface == Application.BUS_INTERFACE
        assert instance.object_path == Application.BUS_PATH
        assert instance.requested_bus_name == Application.BUS_NAME
