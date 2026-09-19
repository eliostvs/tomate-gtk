import dbus
import pytest
from dbus.mainloop.glib import DBusGMainLoop
from dbusmock import DBusTestCase

from tomate.pomodoro import Application
from tomate.pomodoro.app import State
from tomate.pomodoro.composition import create_application_graph
from tomate.pomodoro.graph import Graph
from tomate.pomodoro.plugin import PluginEngine
from tomate.ui import Window

DBusGMainLoop(set_as_default=True)


@pytest.fixture
def application_graph(window, plugin_engine) -> Graph:
    graph = create_application_graph()
    graph.register_instance(Window, window)
    graph.register_instance(PluginEngine, plugin_engine)
    return graph


@pytest.fixture
def app(application_graph, mocker) -> Application:
    instance = Application.from_graph(application_graph, mocker.Mock())
    assert isinstance(instance, Application)
    return instance


def test_collects_plugins_on_start(window, plugin_engine, mocker):
    Application(mocker.Mock(), window, plugin_engine)

    assert plugin_engine.has_plugins() is True


class TestRun:
    def test_start_window_when_app_is_not_running(self, app, window):
        app.state = State.STOPPED

        app.Run()

        window.run.assert_called_once_with()

    def test_shows_window_when_app_is_running(self, app, window):
        app.state = State.STARTED

        app.Run()

        window.show.assert_called_once_with()


class TestFromGraph:
    def setup_method(self):
        DBusTestCase.start_session_bus()

    def teardown_method(self):
        DBusTestCase.tearDownClass()

    def test_create_app_instance_when_it_is_not_registered_in_dbus(self, application_graph):
        instance = Application.from_graph(application_graph, DBusTestCase.get_dbus())

        assert isinstance(instance, Application)

    def test_get_dbus_interface_when_is_registered_in_dbus(self, application_graph):
        Application.from_graph(application_graph, DBusTestCase.get_dbus())

        instance = Application.from_graph(application_graph, DBusTestCase.get_dbus())

        assert isinstance(instance, dbus.Interface)
        assert instance.dbus_interface == Application.BUS_INTERFACE
        assert instance.object_path == Application.BUS_PATH
        assert instance.requested_bus_name == Application.BUS_NAME
