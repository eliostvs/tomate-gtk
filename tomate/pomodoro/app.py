import dbus.service
from wiring import inject
from wiring.scanning import register

from . import State


@register.factory("tomate.app")
class Application(dbus.service.Object):
    BUS_NAME = "com.github.Tomate"
    BUS_PATH = "/com/github/Tomate"
    BUS_INTERFACE = "com.github.Tomate"
    SPEC = "tomate.app"

    @inject(bus="dbus.session", view="tomate.ui.view", plugin="tomate.plugin")
    def __init__(self, bus, view, plugin):
        dbus.service.Object.__init__(self, bus, self.BUS_PATH)
        self.state = State.stopped
        self.window = view
        self.plugin = plugin

        plugin.collectPlugins()

    @dbus.service.method(BUS_INTERFACE, out_signature="b")
    def IsRunning(self):
        return self.state == State.started

    @dbus.service.method(BUS_INTERFACE, out_signature="b")
    def Run(self):
        if self.IsRunning():
            self.window.show()
        else:
            self.state = State.started
            self.window.run()
            self.state = State.stopped

        return True

    @classmethod
    def from_graph(cls, graph):
        bus_session = dbus.SessionBus()
        request = bus_session.request_name(
            cls.BUS_NAME, dbus.bus.NAME_FLAG_DO_NOT_QUEUE
        )

        if request != dbus.bus.REQUEST_NAME_REPLY_EXISTS:
            graph.register_instance("dbus.session", bus_session)
            instance = graph.get(cls.SPEC)
        else:
            bus_object = bus_session.get_object(cls.BUS_NAME, cls.BUS_PATH)
            instance = dbus.Interface(bus_object, cls.BUS_INTERFACE)

        return instance
