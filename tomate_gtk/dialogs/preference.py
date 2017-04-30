from __future__ import unicode_literals

import locale
import logging
from locale import gettext as _

from gi.repository import GdkPixbuf, Gtk
from wiring import inject, SingletonScope
from wiring.scanning import register

locale.textdomain('tomate')
logger = logging.getLogger(__name__)


@register.factory('view.preference', scope=SingletonScope)
class PreferenceDialog(Gtk.Dialog):
    @inject(duration='view.preference.duration', extension='view.preference.extension')
    def __init__(self, duration, extension):
        self.extension = extension
        self.duration = duration

        Gtk.Dialog.__init__(
            self,
            _('Preferences'),
            None,
            modal=True,
            resizable=False,
            window_position=Gtk.WindowPosition.CENTER_ON_PARENT,
        )

        self.set_size_request(350, 200)

        self.connect('response', lambda widget, response: widget.hide())

        stack = Gtk.Stack()
        stack.add_titled(self.duration, 'timer', _('Timer'))

        scrolledwindow = Gtk.ScrolledWindow(shadow_type=Gtk.ShadowType.IN)
        scrolledwindow.add_with_viewport(self.extension.widget)

        stack.add_titled(scrolledwindow, 'extension', _('Extensions'))

        switcher = Gtk.StackSwitcher(margin_top=5,
                                     margin_bottom=5,
                                     halign=Gtk.Align.CENTER)
        switcher.set_stack(stack)

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.pack_start(switcher, True, True, 0)
        vbox.pack_start(separator, True, True, 0)
        vbox.pack_start(stack, True, True, 0)
        vbox.show_all()

        self.get_content_area().add(vbox)

    def refresh_plugin(self):
        self.extension.refresh()


@register.factory('view.preference.duration', scope=SingletonScope)
class TimerDurationStack(Gtk.Grid):
    @inject(config='tomate.config')
    def __init__(self, config):
        self.config = config

        Gtk.Grid.__init__(
            self,
            column_spacing=6,
            margin_bottom=12,
            margin_left=12,
            margin_right=12,
            margin_top=12,
            row_spacing=6,
        )

        section = self._add_section(_('Duration:'))
        self.attach(section, 0, 0, 1, 1)

        # Pomodoro Duration
        label, setting = self._add_setting(_('Pomodoro:'),
                                           Gtk.SpinButton.new_with_range(1, 99, 1),
                                           'pomodoro_duration')
        self.attach(label, 0, 1, 1, 1)
        self.attach_next_to(setting, label, Gtk.PositionType.RIGHT, 3, 1)

        # Short Break Duration
        label, setting = self._add_setting(_('Short break:'),
                                           Gtk.SpinButton.new_with_range(1, 99, 1),
                                           'shortbreak_duration')
        self.attach(label, 0, 2, 1, 1)
        self.attach_next_to(setting, label, Gtk.PositionType.RIGHT, 3, 1)

        # Long Break Duration
        label, setting = self._add_setting(_('Long Break'),
                                           Gtk.SpinButton.new_with_range(1, 99, 1),
                                           'longbreak_duration')
        self.attach(label, 0, 3, 1, 1)
        self.attach_next_to(setting, label, Gtk.PositionType.RIGHT, 3, 1)

    @staticmethod
    def _add_section(name):
        section = Gtk.Label('<b>{0}</b>'.format(name), use_markup=True)
        section.set_halign(Gtk.Align.START)
        return section

    def _add_setting(self, label_name, spinbutton, option):
        label = Gtk.Label(label_name,
                          margin_left=12,
                          hexpand=True,
                          halign=Gtk.Align.END)

        spinbutton.set_hexpand(True)
        spinbutton.set_halign(Gtk.Align.START)
        spinbutton.set_value(self.config.get_int('Timer', option))
        spinbutton.connect('value-changed', self.on_spinbutton_value_changed, option)

        return label, spinbutton

    def on_spinbutton_value_changed(self, widget, option):
        value = str(widget.get_value_as_int())
        self.config.set('Timer', option, value)


@register.factory('view.preference.extension', scope=SingletonScope)
class ExtensionStack(Gtk.Box):
    @inject(plugin='tomate.plugin', config='tomate.config', lazy_proxy='tomate.proxy')
    def __init__(self, plugin, config, lazy_proxy):
        self.plugin = plugin
        self.config = config
        self.view = lazy_proxy('tomate.view')

        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL,
                         spacing=5,
                         margin_left=5,
                         margin_right=5,
                         margin_bottom=5,
                         margin_top=5)

        self.tree_view = Gtk.TreeView(headers_visible=False)
        self.tree_view.get_selection().connect('changed', self.on_tree_view_changed)
        self.tree_view.get_selection().set_mode(Gtk.SelectionMode.BROWSE)

        self._store = Gtk.ListStore(bool,  # active
                                    GdkPixbuf.Pixbuf,  # icon
                                    str,  # name
                                    str,  # detail
                                    object)  # plugin

        self.tree_view.set_model(self._store)

        renderer = Gtk.CellRendererToggle()
        renderer.connect('toggled', self.on_plugin_toggled)
        column = Gtk.TreeViewColumn('Active', renderer, active=0)
        self.tree_view.append_column(column)

        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn('Icon', renderer, pixbuf=1)
        self.tree_view.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Detail', renderer, markup=3)
        self.tree_view.append_column(column)

        self.plugin_settings_button = Gtk.Button.new_from_icon_name(Gtk.STOCK_PREFERENCES, Gtk.IconSize.MENU)
        self.plugin_settings_button.set_sensitive(False)
        self.plugin_settings_button.connect('clicked', self.on_plugin_settings_clicked)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        hbox.pack_end(self.plugin_settings_button, False, True, 0)

        self.pack_start(self.tree_view, True, True, 0)
        self.pack_start(hbox, False, True, 0)

        self.show_all()

    def on_tree_view_changed(self, selection):
        _, treeiter = selection.get_selected()

        if treeiter is not None:
            plugin = self.get_selected_plugin()

            if getattr(plugin.plugin_object, 'has_settings', False) is True:
                logger.debug('Activating settings for plugin %s', plugin.name)
                self.plugin_settings_button.set_sensitive(True)
            else:
                self.plugin_settings_button.set_sensitive(False)

    def get_selected_plugin(self):
        _, treeiter = self.tree_view.get_selection().get_selected()

        grid_plugin = GridPlugin.from_iter(self._store, treeiter)

        plugin = self.plugin.getPluginByName(grid_plugin.name)
        return plugin

    @property
    def toplevel(self):
        return self.view.widget

    def refresh(self):
        self.clear()

        for plugin in self.plugin.getAllPlugins():
            self.add_plugin(plugin)

        if self.there_are_plugins:
            self.select_first_plugin()

    def on_plugin_toggled(self, _, path):
        grid_plugin = GridPlugin.from_path(self._store, path)
        grid_plugin.toggle()

        if grid_plugin.is_enable:
            self.activate_plugin(grid_plugin.name)

        else:
            self.deactivate_plugin(grid_plugin.name)

    def on_plugin_settings_clicked(self, _):
        plugin = self.get_selected_plugin()

        widget = plugin.plugin_object.settings_window()
        widget.set_transient_for(self.toplevel)
        widget.run()

    def deactivate_plugin(self, plugin_name):
        self.plugin.deactivatePluginByName(plugin_name)
        self.plugin_settings_button.set_sensitive(False)

    def activate_plugin(self, plugin_name):
        self.plugin.activatePluginByName(plugin_name)

    def clear(self):
        self._store.clear()

    def select_first_plugin(self):
        self.tree_view.get_selection().select_iter(self._store.get_iter_first())

    @property
    def there_are_plugins(self):
        return bool(len(self._store))

    def add_plugin(self, plugin):
        iconname = getattr(plugin, 'icon', 'tomate-plugin')
        iconpath = self.config.get_icon_path(iconname, 16)

        self._store.append((plugin.plugin_object.is_activated,
                            GridPlugin.pixbuf(iconpath),
                            plugin.name,
                            GridPlugin.markup(plugin),
                            plugin))

        logger.debug('plugin %s added', plugin.name)

    @property
    def widget(self):
        return self


class GridPlugin(object):
    ACTIVE = 0
    TITLE = 2

    def __init__(self, value):
        self._value = value

    @staticmethod
    def from_iter(treestore, treeiter):
        return GridPlugin(treestore[treeiter])

    @staticmethod
    def from_path(treestore, treepath):
        treeiter = treestore.get_iter(treepath)
        return GridPlugin(treestore[treeiter])

    @property
    def name(self):
        return self._value[self.TITLE]

    @property
    def is_enable(self):
        return self._value[self.ACTIVE]

    def toggle(self):
        self._value[self.ACTIVE] = not self._value[self.ACTIVE]

    @staticmethod
    def pixbuf(iconpath):
        return GdkPixbuf.Pixbuf.new_from_file(iconpath)

    @staticmethod
    def markup(plugin):
        return ('<b>{name}</b> ({version})'
                '\n<small>{description}</small>'
                ).format(name=plugin.name,
                         version=plugin.version,
                         description=plugin.description)
