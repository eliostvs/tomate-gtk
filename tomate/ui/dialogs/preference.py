import locale
import logging
from locale import gettext as _

from gi.repository import GdkPixbuf, Gtk, Pango
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import Bus, Config, PluginEngine

locale.textdomain("tomate")
logger = logging.getLogger(__name__)


@register.factory("tomate.ui.preference", scope=SingletonScope)
class PreferenceDialog(Gtk.Dialog):
    @inject(
        timer_tab="tomate.ui.preference.timer",
        extension_tab="tomate.ui.preference.extension",
    )
    def __init__(self, timer_tab, extension_tab):
        stack = Gtk.Stack()
        stack.add_titled(timer_tab.widget, "timer", _("Timer"))
        stack.add_titled(extension_tab.widget, "extension", _("Extensions"))

        switcher = Gtk.StackSwitcher(halign=Gtk.Align.CENTER)
        switcher.props.stack = stack

        content_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_bottom=12)
        content_area.pack_start(switcher, False, False, 0)
        content_area.pack_start(stack, False, False, 0)
        content_area.show_all()

        super().__init__(
            title=_("Preferences"),
            border_width=12,
            resizable=False,
            window_position=Gtk.WindowPosition.CENTER_ON_PARENT,
            flags=Gtk.DialogFlags.MODAL,
        )
        self.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.connect("response", lambda widget, response: widget.hide())
        self.set_size_request(350, -1)
        self.get_content_area().add(content_area)

        stack.set_visible_child_name("timer")

        self._extension_tab = extension_tab
        self._extension_tab.set_toplevel(self)

    @property
    def widget(self):
        return self

    def run(self):
        logger.debug("action=run")
        self._extension_tab.refresh()
        return super().run()


@register.factory("tomate.ui.preference.timer", scope=SingletonScope)
class TimerTab:
    @inject(config="tomate.config")
    def __init__(self, config: Config):
        self._config = config

        section = self._create_section(_("Duration"))
        self.widget = Gtk.Grid(column_spacing=12, row_spacing=6)
        self.widget.attach(section, 0, 0, 1, 1)

        # Pomodoro Duration
        label, button = self._create_option("duration.pomodoro", _("Pomodoro"), Config.DURATION_POMODORO)
        self.widget.attach(label, 0, 1, 1, 1)
        self.widget.attach_next_to(button, label, Gtk.PositionType.RIGHT, 3, 1)
        self.pomodoro = button

        # Short Break Duration
        label, button = self._create_option("duration.shortbreak", _("Short break"), Config.DURATION_SHORT_BREAK)
        self.widget.attach(label, 0, 2, 1, 1)
        self.widget.attach_next_to(button, label, Gtk.PositionType.RIGHT, 3, 1)
        self.shortbreak = button

        # Long Break Duration
        label, button = self._create_option("duration.longbreak", _("Long Break"), Config.DURATION_LONG_BREAK)
        self.widget.attach(label, 0, 3, 1, 1)
        self.widget.attach_next_to(button, label, Gtk.PositionType.RIGHT, 3, 1)
        self.longbreak = button

    def _create_section(self, name):
        section = Gtk.Label.new()
        section.set_markup("<b>{0}</b>".format(name))
        section.props.halign = Gtk.Align.START
        return section

    def _create_option(self, name: str, label: str, option: str):
        label = Gtk.Label.new(label + ":")
        label.set_properties(margin_left=12, hexpand=True, halign=Gtk.Align.END)

        button = Gtk.SpinButton.new_with_range(1, 99, 1)
        button.set_properties(
            hexpand=True, halign=Gtk.Align.START, name=name, value=self._config.get_int("Timer", option)
        )
        button.connect("value-changed", self._on_change, option)

        return label, button

    def _on_change(self, widget, option):
        value = str(widget.get_value_as_int())
        self._config.set("Timer", option, value)


@register.factory("tomate.ui.preference.extension", scope=SingletonScope)
class ExtensionTab:
    @inject(bus="tomate.bus", config="tomate.config", plugin_engine="tomate.plugin")
    def __init__(self, bus: Bus, config: Config, plugin_engine: PluginEngine):
        self._plugins = plugin_engine
        self._config = config
        self._bus = bus
        self.toplevel = None

        self.plugin_model = Gtk.ListStore(*PluginGrid.MODEL)

        self.plugin_list = Gtk.TreeView(headers_visible=False, model=self.plugin_model, name="plugin.list")
        self.plugin_list.get_selection().connect("changed", self._on_plugin_changed)
        self.plugin_list.get_selection().set_mode(Gtk.SelectionMode.BROWSE)

        renderer = Gtk.CellRendererToggle()
        renderer.connect("toggled", self._on_plugin_toggle)
        column = Gtk.TreeViewColumn("Active", renderer, active=PluginGrid.ACTIVE)
        self.plugin_list.append_column(column)

        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn("Icon", renderer, pixbuf=PluginGrid.ICON)
        self.plugin_list.append_column(column)

        renderer = Gtk.CellRendererText(wrap_mode=Pango.WrapMode.WORD, wrap_width=250)
        column = Gtk.TreeViewColumn("Detail", renderer, markup=PluginGrid.DETAIL)
        self.plugin_list.append_column(column)

        plugin_list_container = Gtk.ScrolledWindow(shadow_type=Gtk.ShadowType.IN)
        plugin_list_container.add(self.plugin_list)

        self.settings_button = Gtk.Button.new_from_icon_name(Gtk.STOCK_PREFERENCES, Gtk.IconSize.MENU)
        self.settings_button.set_properties(name="plugin.settings", sensitive=False)
        self.settings_button.connect("clicked", self._on_plugin_settings_clicked)

        settings_button_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        settings_button_container.pack_end(self.settings_button, False, False, 0)

        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.widget.pack_start(plugin_list_container, True, True, 0)
        self.widget.pack_start(settings_button_container, False, False, 0)

        self.widget.show_all()

    def _on_plugin_changed(self, selection):
        model, selected = selection.get_selected()

        if selected is not None:
            grid_plugin = PluginGrid.from_iter(model, selected)
            self.settings_button.props.sensitive = grid_plugin.is_enable & grid_plugin.has_settings

    def _on_plugin_toggle(self, _, path):
        plugin = PluginGrid.from_path(self.plugin_model, path)
        plugin.toggle()

        logger.debug("action=toggle plugin=%s enable=%s", plugin.name, plugin.is_enable)

        if plugin.is_enable:
            self._activate(plugin)
        else:
            self._deactivate(plugin)

    def _on_plugin_settings_clicked(self, _):
        model, selected = self.plugin_list.get_selection().get_selected()
        grid_plugin = PluginGrid.from_iter(model, selected)
        logger.debug("action=open_plugin_settings plugin=%s", grid_plugin.name)
        grid_plugin.open_settings(self.toplevel)

    def _activate(self, plugin):
        plugin.instance.connect(self._bus)
        self._plugins.activate(plugin.name)
        self.settings_button.props.sensitive = plugin.has_settings

    def _deactivate(self, plugin):
        plugin.instance.disconnect(self._bus)
        self._plugins.deactivate(plugin.name)
        self.settings_button.props.sensitive = False

    def set_toplevel(self, widget: Gtk.Widget) -> None:
        self.toplevel = widget

    def refresh(self):
        logger.debug("action=refresh_plugins has_plugins=%s", self._plugins.has_plugins())

        self._clear()

        for plugin in self._plugins.all():
            self._add(plugin)

        if self._plugins.has_plugins():
            self._select_first()

    def _add(self, plugin):
        logger.debug("action=add_plugin plugin=%s", plugin.name)
        self.plugin_model.append(PluginGrid.create_row(plugin, self._config))
        if plugin.is_activated:
            plugin.plugin_object.connect(self._bus)

    def _select_first(self):
        self.plugin_list.get_selection().select_iter(self.plugin_model.get_iter_first())

    def _clear(self):
        logger.debug("action=clear_plugin_list")
        self.plugin_model.clear()


class PluginGrid(object):
    NAME = 0
    ACTIVE = 1
    ICON = 2
    DETAIL = 3
    INSTANCE = 4
    MODEL = [
        str,
        bool,
        GdkPixbuf.Pixbuf,
        str,
        object,
    ]  # name active icon detail instance

    def __init__(self, row):
        self._row = row

    @property
    def name(self):
        return self._row[self.NAME]

    @property
    def is_enable(self):
        return self._row[self.ACTIVE]

    def toggle(self):
        self._row[self.ACTIVE] = not self._row[self.ACTIVE]

    @property
    def instance(self):
        return self._row[self.INSTANCE]

    @property
    def has_settings(self):
        return getattr(self._row[self.INSTANCE], "has_settings", False)

    def open_settings(self, toplevel):
        self.instance.settings_window(toplevel).run()

    @staticmethod
    def create_row(plugin, config):
        return [
            plugin.name,
            plugin.plugin_object.is_activated,
            PluginGrid.pixbuf(plugin, config),
            PluginGrid.description(plugin),
            plugin.plugin_object,
        ]

    @staticmethod
    def pixbuf(plugin, config):
        icon_name = getattr(plugin, "icon", "tomate-plugin")
        icon_path = config.icon_path(icon_name, 16)
        return GdkPixbuf.Pixbuf.new_from_file(icon_path)

    @staticmethod
    def description(plugin):
        return "<b>{name}</b> ({version})" "\n<small>{description}</small>".format(
            name=plugin.name, version=plugin.version, description=plugin.description
        )

    @classmethod
    def from_iter(cls, tree_store, tree_iter):
        return cls(tree_store[tree_iter])

    @classmethod
    def from_path(cls, tree_store, tree_path):
        tree_iter = tree_store.get_iter(tree_path)
        return cls(tree_store[tree_iter])
