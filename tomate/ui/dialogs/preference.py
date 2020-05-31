import locale
import logging
from locale import gettext as _

from gi.repository import GdkPixbuf, Gtk, Pango
from wiring import inject, SingletonScope
from wiring.scanning import register

locale.textdomain("tomate")
logger = logging.getLogger(__name__)


@register.factory("tomate.ui.preference", scope=SingletonScope)
class PreferenceDialog:
    @inject(
        duration="tomate.ui.preference.timer",
        extension="tomate.ui.preference.extension",
    )
    def __init__(self, duration, extension):
        self._extension = extension

        self.widget = Gtk.Dialog(
            title=_("Preferences"),
            border_width=11,
            modal=True,
            resizable=False,
            window_position=Gtk.WindowPosition.CENTER_ON_PARENT,
        )
        self.widget.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.widget.connect("response", lambda widget, response: widget.hide())
        self.widget.set_size_request(350, -1)

        stack = Gtk.Stack()
        stack.add_titled(duration.widget, "timer", _("Timer"))

        stack.add_titled(self._extension.widget, "extension", _("Extensions"))

        switcher = Gtk.StackSwitcher(halign=Gtk.Align.CENTER)
        switcher.set_stack(stack)

        content_area = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_bottom=12
        )
        content_area.pack_start(switcher, False, False, 0)
        content_area.pack_start(stack, False, False, 0)
        content_area.show_all()

        self.widget.get_content_area().add(content_area)

        stack.set_visible_child_name("timer")

    def run(self):
        self._extension.refresh()
        self.widget.run()


@register.factory("tomate.ui.preference.timer", scope=SingletonScope)
class TimerTab:
    @inject(config="tomate.config")
    def __init__(self, config):
        self._config = config

        self.widget = Gtk.Grid(column_spacing=12, row_spacing=6)

        section = self._create_section(_("Duration"))
        self.widget.attach(section, 0, 0, 1, 1)

        # Pomodoro Duration
        label, button = self._add_setting(_("Pomodoro"), "pomodoro_duration")
        self.widget.attach(label, 0, 1, 1, 1)
        self.widget.attach_next_to(button, label, Gtk.PositionType.RIGHT, 3, 1)
        self.pomodoro_duration = button

        # Short Break Duration
        label, button = self._add_setting(_("Short break"), "shortbreak_duration")
        self.widget.attach(label, 0, 2, 1, 1)
        self.widget.attach_next_to(button, label, Gtk.PositionType.RIGHT, 3, 1)
        self.shortbreak_duration = button

        # Long Break Duration
        label, button = self._add_setting(_("Long Break"), "longbreak_duration")
        self.widget.attach(label, 0, 3, 1, 1)
        self.widget.attach_next_to(button, label, Gtk.PositionType.RIGHT, 3, 1)
        self.longbreak_duration = button

    def _create_section(self, name):
        section = Gtk.Label.new()
        section.set_markup("<b>{0}</b>".format(name))
        section.set_halign(Gtk.Align.START)

        return section

    def _add_setting(self, label_name, option):
        label = Gtk.Label.new(label_name + ":")
        label.set_properties(margin_left=12, hexpand=True, halign=Gtk.Align.END)

        button = Gtk.SpinButton.new_with_range(1, 99, 1)
        button.set_hexpand(True)
        button.set_halign(Gtk.Align.START)
        button.set_value(self._config.get_int("Timer", option))
        button.connect("value-changed", self._on_value_changed, option)

        return label, button

    def _on_value_changed(self, widget, option):
        value = str(widget.get_value_as_int())
        self._config.set("Timer", option, value)


@register.factory("tomate.ui.preference.extension", scope=SingletonScope)
class ExtensionTab:
    @inject(
        plugin_manager="tomate.plugin",
        config="tomate.config",
        lazy_proxy="tomate.proxy",
    )
    def __init__(self, plugin_manager, config, lazy_proxy):
        self._plugin_manager = plugin_manager
        self._config = config
        self._preference_dialog = lazy_proxy("tomate.ui.preference")

        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self._store = Gtk.ListStore(
            bool,  # activate
            GdkPixbuf.Pixbuf,  # icon
            str,  # name
            str,  # detail
            object,  # plugin instance
        )

        self._plugin_list = Gtk.TreeView(headers_visible=False, model=self._store)
        self._plugin_list.get_selection().connect("changed", self._on_tree_view_changed)
        self._plugin_list.get_selection().set_mode(Gtk.SelectionMode.BROWSE)

        renderer = Gtk.CellRendererToggle()
        renderer.connect("toggled", self._on_plugin_toggled)
        column = Gtk.TreeViewColumn("Active", renderer, active=0)
        self._plugin_list.append_column(column)

        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn("Icon", renderer, pixbuf=1)
        self._plugin_list.append_column(column)

        renderer = Gtk.CellRendererText(wrap_mode=Pango.WrapMode.WORD, wrap_width=250)
        column = Gtk.TreeViewColumn("Detail", renderer, markup=3)
        self._plugin_list.append_column(column)

        self._settings_button = Gtk.Button.new_from_icon_name(
            Gtk.STOCK_PREFERENCES, Gtk.IconSize.MENU
        )
        self._settings_button.set_sensitive(False)
        self._settings_button.connect("clicked", self._on_plugin_settings_clicked)

        plugin_list_container = Gtk.ScrolledWindow(shadow_type=Gtk.ShadowType.IN)
        plugin_list_container.add(self._plugin_list)

        settings_button_container = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6
        )
        settings_button_container.pack_end(self._settings_button, False, False, 0)

        self.widget.pack_start(plugin_list_container, True, True, 0)
        self.widget.pack_start(settings_button_container, False, False, 0)

        self.widget.show_all()

    def refresh(self):
        self._clear()

        for plugin in self._plugin_manager.getAllPlugins():
            logger.debug("action=refresh")
            self._add_plugin(plugin)

        if self._there_are_plugins:
            self._select_first_plugin()

    def _on_tree_view_changed(self, selection):
        _, treeiter = selection.get_selected()

        if treeiter is not None:
            plugin = self.get_selected_plugin()

            if getattr(plugin.plugin_object, "has_settings", False) is True:
                self._settings_button.set_sensitive(True)
            else:
                self._settings_button.set_sensitive(False)

    def get_selected_plugin(self):
        _, treeiter = self._plugin_list.get_selection().get_selected()

        grid_plugin = GridPlugin.from_iter(self._store, treeiter)

        return self._plugin_manager.getPluginByName(grid_plugin.name)

    @property
    def toplevel(self):
        return self._preference_dialog.widget

    def _on_plugin_toggled(self, _, path):
        grid_plugin = GridPlugin.from_path(self._store, path)
        grid_plugin.toggle()

        if grid_plugin.is_enable:
            self._activate_plugin(grid_plugin.name)
        else:
            self._deactivate_plugin(grid_plugin.name)

    def _on_plugin_settings_clicked(self, _):
        plugin = self.get_selected_plugin()

        widget = plugin.plugin_object.settings_window()
        widget.set_transient_for(self.toplevel)
        widget.run()

    def _deactivate_plugin(self, plugin_name):
        self._plugin_manager.deactivatePluginByName(plugin_name)
        self._settings_button.set_sensitive(False)

    def _activate_plugin(self, plugin_name):
        self._plugin_manager.activatePluginByName(plugin_name)

    def _clear(self):
        self._store.clear()

    def _select_first_plugin(self):
        self._plugin_list.get_selection().select_iter(self._store.get_iter_first())

    @property
    def _there_are_plugins(self):
        return bool(len(self._store))

    def _add_plugin(self, plugin):
        icon_name = getattr(plugin, "icon", "tomate-plugin")
        icon_path = self._config.get_icon_path(icon_name, 16)

        self._store.append(
            (
                plugin.plugin_object.is_activated,
                GridPlugin.pixbuf(icon_path),
                plugin.name,
                GridPlugin.markup(plugin),
                plugin,
            )
        )

        logger.debug("action=addPlugin name=%s", plugin.name)


class GridPlugin(object):
    ACTIVE = 0
    TITLE = 2

    def __init__(self, value):
        self._value = value

    @property
    def name(self):
        return self._value[self.TITLE]

    @property
    def is_enable(self):
        return self._value[self.ACTIVE]

    def toggle(self):
        self._value[self.ACTIVE] = not self._value[self.ACTIVE]

    @staticmethod
    def pixbuf(icon_path):
        return GdkPixbuf.Pixbuf.new_from_file(icon_path)

    @staticmethod
    def markup(plugin):
        return "<b>{name}</b> ({version})" "\n<small>{description}</small>".format(
            name=plugin.name, version=plugin.version, description=plugin.description
        )

    @staticmethod
    def from_iter(treestore, treeiter):
        return GridPlugin(treestore[treeiter])

    @staticmethod
    def from_path(treestore, treepath):
        treeiter = treestore.get_iter(treepath)
        return GridPlugin(treestore[treeiter])
