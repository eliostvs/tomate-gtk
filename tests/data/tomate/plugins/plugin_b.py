from tomate.pomodoro import Event, Events, on, plugin


class PluginB(plugin.Plugin):
    has_settings = False

    @on(Events.WINDOW_SHOW)
    def listener(self, _event: Event[None]) -> str:
        self.last_event = _event
        return "plugin_b"
