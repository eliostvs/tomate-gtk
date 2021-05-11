import tomate.pomodoro.plugin as plugin
from tomate.pomodoro import Events, on


class PluginB(plugin.Plugin):
    has_settings = False

    @on(Events.WINDOW_SHOW)
    def listener(self, **__) -> str:
        return "plugin_b"
