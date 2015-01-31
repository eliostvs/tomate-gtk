from __future__ import unicode_literals

import locale
import logging
from locale import gettext as _

from gi.repository import GdkPixbuf, Gtk
from tomate.profile import ProfileManagerSingleton
from tomate.signals import tomate_signals
from yapsy.PluginManager import PluginManagerSingleton

locale.textdomain('tomate')

logger = logging.getLogger(__name__)

profile = ProfileManagerSingleton.get()


class PreferenceDialog(Gtk.Dialog):

    def __init__(self, parent):
        Gtk.Dialog.__init__(
            self,
            _('Preferences'),
            parent,
            buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE),
            modal=True,
            resizable=False,
            transient_for=parent,
            window_position=Gtk.WindowPosition.CENTER_ON_PARENT,
        )

        self.set_size_request(350, 200)

        self.connect('response', self.on_dialog_response)

        stack = Gtk.Stack()
        stack.add_titled(TimerDurationGrid(), 'timer', _('Timer'))

        self.plugin_list = PluginList()
        scrolledwindow = Gtk.ScrolledWindow(shadow_type=Gtk.ShadowType.OUT)
        scrolledwindow.add_with_viewport(self.plugin_list)

        stack.add_titled(scrolledwindow, 'extension', _('Extensions'))

        switcher = Gtk.StackSwitcher(margin_top=5,
                                     margin_bottom=5,
                                     halign=Gtk.Align.CENTER)
        switcher.set_stack(stack)

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.pack_start(switcher, True, True, 0)
        box.pack_start(separator, True, True, 0)
        box.pack_start(stack, True, True, 0)
        box.show_all()

        content_area = self.get_content_area()
        content_area.add(box)

    def on_dialog_response(self, widget, parameter):
        widget.destroy()

    def refresh_plugin(self):
        self.plugin_list.refresh()


class TimerDurationGrid(Gtk.Grid):

    def __init__(self):
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

        # Pomodoro Lenght Setting
        spinbutton = Gtk.SpinButton.new_with_range(1, 99, 1)
        label, setting = self._add_setting(_('Pomodoro:'),
                                           spinbutton,
                                           'pomodoro_duration')
        self.attach(label, 0, 1, 1, 1)
        self.attach_next_to(setting, label, Gtk.PositionType.RIGHT, 3, 1)

        # Short Break Letting Setting
        spinbutton = Gtk.SpinButton.new_with_range(1, 99, 1)
        label, setting = self._add_setting(_('Short break:'),
                                           spinbutton,
                                           'shortbreak_duration')
        self.attach(label, 0, 2, 1, 1)
        self.attach_next_to(setting, label, Gtk.PositionType.RIGHT, 3, 1)

        # Long Break Lenght Setting
        spinbutton = Gtk.SpinButton.new_with_range(1, 99, 1)
        label, setting = self._add_setting(_('Long Break'),
                                           spinbutton,
                                           'longbreak_duration')
        self.attach(label, 0, 3, 1, 1)
        self.attach_next_to(setting, label, Gtk.PositionType.RIGHT, 3, 1)

    def _add_section(self, name):
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
        spinbutton.set_value(profile.get_int('Timer', option))
        spinbutton.connect('value-changed', self.on_spinbutton_value_changed, option)

        return label, spinbutton

    def on_spinbutton_value_changed(self, widget, option):
        value = widget.get_value_as_int()

        tomate_signals.emit('setting_changed',
                            section='Timer',
                            option=option,
                            value=str(value))

        logger.debug('Session %s duration change to %d', option, value)


class PluginList(Gtk.TreeView):

    def __init__(self):
        Gtk.TreeView.__init__(self, headers_visible=False)

        self.get_selection().set_mode(Gtk.SelectionMode.BROWSE)

        self._store = Gtk.ListStore(bool,  # active
                                    GdkPixbuf.Pixbuf,  # icon
                                    str,   # name
                                    str,   # detail
                                    object)  # plugin

        self.set_model(self._store)

        renderer = Gtk.CellRendererToggle()
        renderer.connect('toggled', self.on_plugin_toggled)
        column = Gtk.TreeViewColumn('Active', renderer, active=0)
        self.append_column(column)

        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn('Icon', renderer, pixbuf=1)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Detail', renderer, markup=3)
        self.append_column(column)

        self.manager = PluginManagerSingleton.get()

    def refresh(self):
        self.clear()

        for plugin in self.manager.getAllPlugins():
            self.add_plugin(plugin)

        if self.there_are_plugins:
            self.select_first_plugin()

    def on_plugin_toggled(self, widget, path):
        plugin = Plugin(self._store, path)

        plugin.toggle()

        if plugin.is_enable:
            self.manager.activatePluginByName(plugin.name)

        else:
            self.manager.deactivatePluginByName(plugin.name)

    def clear(self):
        self._store.clear()

    def select_first_plugin(self):
        self.get_selection().select_iter(self._store.get_iter_first())

    @property
    def there_are_plugins(self):
        return bool(len(self._store))

    def add_plugin(self, plugin):
        self._store.append((plugin.plugin_object.is_activated,
                            Plugin.pixbuf(plugin),
                            plugin.name,
                            Plugin.markup(plugin),
                            plugin))

        logger.debug('plugin %s added', plugin.name)


class Plugin(object):

    ENABLE = 0
    TITLE = 2

    def __init__(self, treestore, treepath):
        treeiter = treestore.get_iter(treepath)
        self._instance = treestore[treeiter]

    @property
    def name(self):
        return self._instance[self.TITLE]

    @property
    def is_enable(self):
        return self._instance[self.ENABLE]

    def toggle(self):
        self._instance[self.ENABLE] = not self._instance[self.ENABLE]

    @staticmethod
    def pixbuf(plugin):
        icon_name = getattr(plugin, 'icon', 'libpeas-plugin')
        icon_path = profile.get_icon_path(icon_name, 16)
        return GdkPixbuf.Pixbuf.new_from_file(icon_path)

    @staticmethod
    def markup(plugin):
        return ('<b>{name}</b> ({version})'
                '\n<small>{description}</small>'
                ).format(name=plugin.name,
                         version=plugin.version,
                         description=plugin.description)
