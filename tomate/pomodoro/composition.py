from tomate.ui import SysTray, SystrayMenu, Window

from .app import Application
from .clock import Clock, SystemClock
from .config import Config
from .event import Bus
from .graph import Graph, Injected
from .id import IDFactory, UUIDFactory
from .plugin import PluginEngine, Resolve
from .session import Session
from .timer import Timer


def create_backbone_graph() -> Graph:
    graph = Graph()
    graph.register_factory(Clock, SystemClock)
    graph.register_factory(IDFactory, UUIDFactory)
    graph.register_factory(Bus, Bus)
    graph.register_factory(Config, Config)
    graph.register_factory(Timer, Timer)
    graph.register_factory(Session, Session)
    return graph


def create_application_graph() -> Graph:
    graph = create_backbone_graph()
    graph.register_instance(Resolve, graph.resolve)
    graph.register_factory(PluginEngine, PluginEngine)
    graph.register_factory(SysTray, SysTray)
    graph.register_factory(Window, Window)
    graph.register_factory(SystrayMenu, _create_systray_menu)
    graph.register_factory(Application, Application)
    return graph


def _create_systray_menu(bus: Injected[Bus], window: Injected[Window]) -> SystrayMenu:
    return SystrayMenu(bus, window)
