from __future__ import unicode_literals

import locale
import logging
from locale import gettext as _

from gi.repository import Gtk
from tomate.profile import ProfileManagerSingleton
from tomate.signals import session_duration_changed
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

        self.set_size_request(370, 200)
        self.connect('response', self.on_dialog_response)

        stack = Gtk.Stack()
        stack.add_titled(TimerDurationGrid(), 'timer', _('Timer'))

        scrolledwindow = Gtk.ScrolledWindow(shadow_type=Gtk.ShadowType.OUT)
        scrolledwindow.add_with_viewport(PluginTreeView())

        stack.add_titled(scrolledwindow, 'plugin', _('Plugins'))

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
        label, setting = self._add_setting(_('Timer:'),
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

        session_duration_changed.send(self.__class__,
                                      section='Timer',
                                      option=option,
                                      value=str(value))

        logger.debug('Session %s duration change to %d', option, value)


class PluginTreeView(Gtk.TreeView):

    def __init__(self):
        Gtk.TreeView.__init__(self)

        self.set_headers_visible(True)

        self.get_selection().set_mode(Gtk.SelectionMode.BROWSE)

        self._store = Gtk.ListStore(bool, str, str, str, object)

        self.set_model(self._store)

        renderer = Gtk.CellRendererToggle()
        renderer.connect('toggled', self.on_active_toggled)
        column = Gtk.TreeViewColumn(_('Active'), renderer, active=0)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_('Version'), renderer, text=1)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_('Name'), renderer, text=2)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(('Description'), renderer, text=3)
        self.append_column(column)

        self.refresh()

    def on_active_toggled(self, widget, path):
        iter = self._store.get_iter(path)
        self._store[iter][0] = not self._store[iter][0]

        manager = PluginManagerSingleton.get()

        if self._store[iter][0]:
            manager.activatePluginByName(self._store[iter][2])

        else:
            manager.deactivatePluginByName(self._store[iter][2])

    def refresh(self):
        self._store.clear()

        manager = PluginManagerSingleton.get()

        for plugin in manager.getAllPlugins():
            self._store.append((plugin.plugin_object.is_activated,
                                str(plugin.version),
                                plugin.name,
                                plugin.description,
                                plugin))

            logger.debug('load plugin in grid %s', plugin.name)

        if len(self._store):
            self.get_selection().select_iter(self._store.get_iter_first())
