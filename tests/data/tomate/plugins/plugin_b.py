from tomate.pomodoro import Events, on, plugin


class PluginB(plugin.Plugin):
    has_settings = False

    @on(Events.WINDOW_SHOW)
    def listener(self, **__) -> str:
        return "plugin_b"
