import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from wiring import inject, SingletonScope
from wiring.scanning import register

from . import State


@register.factory("tomate.app", scope=SingletonScope)
class Application(dbus.service.Object):
    BUS_NAME = "com.github.Tomate"
    BUS_PATH = "/com/github/Tomate"
    BUS_INTERFACE = "com.github.Tomate"
    SPEC = "tomate.app"

    @inject(bus="dbus.session", view="tomate.ui.view", plugin="tomate.plugin")
    def __init__(self, bus, view, plugin):
        dbus.service.Object.__init__(self, bus, self.BUS_PATH)
        self.state = State.stopped
        self.view = view

        plugin.collectPlugins()

    @dbus.service.method(BUS_INTERFACE, out_signature="b")
    def IsRunning(self):
        return self.state == State.started

    @dbus.service.method(BUS_INTERFACE, out_signature="b")
    def Run(self):
        if self.IsRunning():
            self.view.show()
        else:
            self.state = State.started
            self.view.run()

        return True

    @classmethod
    def from_graph(cls, graph, bus=dbus.SessionBus(mainloop=DBusGMainLoop())):
        request = bus.request_name(cls.BUS_NAME, dbus.bus.NAME_FLAG_DO_NOT_QUEUE)

        if request != dbus.bus.REQUEST_NAME_REPLY_EXISTS:
            graph.register_instance("dbus.session", bus)
            instance = graph.get(cls.SPEC)
        else:
            bus_object = bus.get_object(cls.BUS_NAME, cls.BUS_PATH)
            instance = dbus.Interface(bus_object, cls.BUS_INTERFACE)

        return instance
