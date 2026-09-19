from __future__ import annotations

import enum

import dbus.bus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

from tomate.ui.window import Window

from .dbus import SessionBus
from .graph import Graph, Injected
from .plugin import PluginEngine


class State(enum.Enum):
    STOPPED = 1
    STARTED = 2


class Application(dbus.service.Object):
    BUS_NAME = "com.github.Tomate"
    BUS_PATH = "/com/github/Tomate"
    BUS_INTERFACE = "com.github.Tomate"
    def __init__(
        self,
        bus: Injected[SessionBus],
        window: Injected[Window],
        plugins: Injected[PluginEngine],
    ) -> None:
        dbus.service.Object.__init__(self, bus, self.BUS_PATH)
        self.state = State.STOPPED
        self._window = window
        plugins.collect()

    @dbus.service.method(BUS_INTERFACE, out_signature="b")
    def IsRunning(self):
        return self.state == State.STARTED

    @dbus.service.method(BUS_INTERFACE, out_signature="b")
    def Run(self):
        if self.IsRunning():
            self._window.show()
        else:
            self.state = State.STARTED
            self._window.run()

        return True

    @classmethod
    def from_graph(cls, graph: Graph, bus: SessionBus | None = None) -> Application | dbus.Interface:
        if bus is None:
            bus = dbus.SessionBus(mainloop=DBusGMainLoop())

        request = bus.request_name(cls.BUS_NAME, dbus.bus.NAME_FLAG_DO_NOT_QUEUE)

        if request != dbus.bus.REQUEST_NAME_REPLY_EXISTS:
            graph.register_instance(SessionBus, bus)
            instance = graph.resolve(cls)
        else:
            bus_object = bus.get_object(cls.BUS_NAME, cls.BUS_PATH)
            instance = dbus.Interface(bus_object, cls.BUS_INTERFACE)

        return instance
