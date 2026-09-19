from tomate.pomodoro.app import Application
from tomate.pomodoro.clock import Clock
from tomate.pomodoro.composition import create_application_graph, create_backbone_graph
from tomate.pomodoro.config import Config
from tomate.pomodoro.event import Bus
from tomate.pomodoro.id import IDFactory
from tomate.pomodoro.plugin import PluginEngine, Resolve
from tomate.pomodoro.session import Session
from tomate.pomodoro.timer import Timer
from tomate.ui import SysTray, SystrayMenu, Window


def test_backbone_graph_registers_only_the_core_services():
    graph = create_backbone_graph()

    assert graph._providers.keys() == {
        Clock,
        IDFactory,
        Bus,
        Config,
        Timer,
        Session,
    }


def test_application_graph_registers_backbone_and_application_services():
    graph = create_application_graph()

    assert graph._providers.keys() == {
        Clock,
        IDFactory,
        Bus,
        Config,
        Timer,
        Session,
        Resolve,
        PluginEngine,
        SysTray,
        Window,
        SystrayMenu,
        Application,
    }


def test_composition_registers_the_systray_menu(window):
    graph = create_application_graph()
    graph.register_instance(Window, window)

    assert isinstance(graph.resolve(SystrayMenu), SystrayMenu)
