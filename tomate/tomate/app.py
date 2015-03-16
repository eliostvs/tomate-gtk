from __future__ import unicode_literals

import dbus.service
from wiring import implements, inject, Interface

from .enums import State


class IApplication(Interface):

    state = ''

    def is_running():
        pass

    def run():
        pass


@implements(IApplication)
class Application(dbus.service.Object):

    bus_name = 'com.github.Tomate'
    bus_object_path = '/'
    bus_interface_name = 'com.github.Tomate'

    @inject(bus='dbus.session',
            view='tomate.view',
            config='tomate.config',
            plugin='tomate.plugin')
    def __init__(self, bus, view, config, plugin):
        dbus.service.Object.__init__(self, bus, self.bus_object_path)
        self.state = State.stopped
        self.config = config
        self.view = view
        self.plugin = plugin

        self.plugin.setPluginPlaces(self.config.get_plugin_paths())
        self.plugin.setPluginInfoExtension('plugin')
        self.plugin.setConfigParser(self.config.parser, self.config.save)
        self.plugin.collectPlugins()

    @dbus.service.method(bus_interface_name, out_signature='b')
    def is_running(self):
        return self.state == State.running

    @dbus.service.method(bus_interface_name, out_signature='b')
    def run(self):
        if self.is_running():
            self.view.show()

        else:
            self.state = State.running
            self.view.run()
            self.state = State.stopped

        return True


def application_factory(graph, specification='tomate.app'):
    bus_session = dbus.SessionBus()
    app_class = graph.providers[specification].factory

    request = bus_session.request_name(app_class.bus_name,
                                       dbus.bus.NAME_FLAG_DO_NOT_QUEUE)

    if request != dbus.bus.REQUEST_NAME_REPLY_EXISTS:
        graph.register_instance('dbus.session', bus_session)
        app = graph.get(specification)

    else:
        bus_object = bus_session.get_object(app_class.bus_name,
                                            app_class.bus_object_path)

        app = dbus.Interface(bus_object, app_class.bus_interface_name)

    return app
