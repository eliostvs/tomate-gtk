import dbus.service
from wiring import inject
from wiring.scanning import register

from .constant import State


@register.factory("tomate.app")
class Application(dbus.service.Object):
    bus_name = "com.github.Tomate"
    bus_object_path = "/"
    bus_interface_name = "com.github.Tomate"
    specification = "tomate.app"

    @inject(bus="dbus.session", view="tomate.ui.view", plugin="tomate.plugin")
    def __init__(self, bus, view, plugin):
        dbus.service.Object.__init__(self, bus, self.bus_object_path)
        self.state = State.stopped
        self.window = view
        self.plugin = plugin

        plugin.collectPlugins()

    @dbus.service.method(bus_interface_name, out_signature="b")
    def is_running(self):
        return self.state == State.started

    @dbus.service.method(bus_interface_name, out_signature="b")
    def run(self):
        if self.is_running():
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
            cls.bus_name, dbus.bus.NAME_FLAG_DO_NOT_QUEUE
        )

        if request != dbus.bus.REQUEST_NAME_REPLY_EXISTS:
            graph.register_instance("dbus.session", bus_session)
            instance = graph.get(cls.specification)

        else:
            bus_object = bus_session.get_object(cls.bus_name, cls.bus_object_path)
            instance = dbus.Interface(bus_object, cls.bus_interface_name)

        return instance
