from __future__ import unicode_literals

import locale
import logging
from locale import gettext as _

from gi.repository import GdkPixbuf, Gtk
from tomate.mixins import ConnectSignalMixin
from tomate.pomodoro import Task
from tomate.profile import ProfileManager
from tomate.services import Cache
from tomate.utils import format_time_left

from .about import AboutDialog
from .modebutton import ModeButton
from .preference import PreferenceDialog

locale.textdomain('tomate')

logger = logging.getLogger(__name__)

profile = ProfileManager()


class Window(Gtk.Window):

    iconpath = profile.get_icon_path('tomate', 22)

    def __init__(self):
        Gtk.Window.__init__(
            self,
            title='Tomate',
            icon=GdkPixbuf.Pixbuf.new_from_file(self.iconpath),
            window_position=Gtk.WindowPosition.CENTER,
            resizable=False
        )
        self.set_size_request(350, -1)

        self.connect('delete-event', self.on_window_delete_event)

        self.menu = MainMenu(self)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(Toolbar(self), False, False, 0)
        box.pack_start(TimerFrame(), True, True, 0)
        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL),
                       False, False, 8)
        box.pack_start(TaskButtons(), True, True, 0)

        self.add(box)

        self.app = Cache.get('GtkApplication')

        self.show_all()

    def on_window_delete_event(self, window, event):
        return self.app.quit()

    def show_window(self):
        return self.present()


class TaskButtons(ConnectSignalMixin, ModeButton):

        signals = (
            ('session_started', 'disable'),
            ('session_interrupted', 'enable'),
            ('session_ended', 'change_selected'),
            ('session_ended', 'enable'),
        )

        def __init__(self):
            ModeButton.__init__(
                self,
                can_focus=False,
                homogeneous=True,
                margin_bottom=12,
                margin_left=12,
                margin_right=12,
                margin_top=4,
                spacing=0,
            )

            self.append_text(_('Pomodoro'))
            self.append_text(_('Short Break'))
            self.append_text(_('Long Break'))
            self.set_selected(0)

            self.connect('mode_changed', self.on_mode_changed)

            self.app = Cache.get('GtkApplication')

            self.connect_signals()

        def on_mode_changed(self, widget, index):
            task = Task.get_by_index(index)
            self.app.change_task(task=task)

        def change_selected(self, sender=None, **kwargs):
            task = kwargs.get('task', Task.pomodoro)

            logger.debug('task changed %s', task)

            self.set_selected(task.value)

        def disable(self, sender=None, **kwargs):
            self.set_sensitive(False)

        def enable(self, sender=None, **kwargs):
            self.set_sensitive(True)


class TimerFrame(ConnectSignalMixin, Gtk.Frame):

        signals = (
            ('session_ended', 'update_session'),
            ('sessions_reseted', 'update_session'),
            ('session_interrupted', 'update_timer'),
            ('task_changed', 'update_timer'),
            ('timer_updated', 'update_timer'),
        )

        def __init__(self):
            Gtk.Frame.__init__(
                self,
                margin_bottom=2,
                margin_left=12,
                margin_right=12,
                margin_top=12,
                shadow_type=Gtk.ShadowType.IN,
            )

            self.timer_label = Gtk.Label(justify=Gtk.Justification.CENTER,
                                         hexpand=True,
                                         vexpand=True,
                                         halign=Gtk.Align.FILL,
                                         valign=Gtk.Align.FILL)

            self.sessions_label = Gtk.Label(justify=Gtk.Justification.CENTER,
                                            margin_bottom=12,
                                            hexpand=True)
            box = Gtk.VBox()
            box.pack_start(self.timer_label, True, True, 0)
            box.pack_start(self.sessions_label, False, False, 0)

            self.add(box)

            self.update_session(0)

            self.connect_signals()

        def update_timer(self, sender=None, **kwargs):
            time_left = format_time_left(kwargs.get('time_left', 25 * 60))

            markup = '<span font="60">{}</span>'.format(time_left)
            self.timer_label.set_markup(markup)

            logger.debug('timer label update %s', time_left)

        def update_session(self, sender=None, **kwargs):
            sessions = kwargs.get('sessions', 0)

            markup = ('<span font="12">{0} pomodoros</span>'
                      .format(sessions))

            self.sessions_label.set_markup(markup)

            logger.debug('session label update %s', sessions)


class Toolbar(ConnectSignalMixin, Gtk.Toolbar):

    signals = (
        ('session_ended', 'enable_start_button'),
        ('sessions_reseted', 'disable_reset_button'),
        ('session_started', 'enable_interrupt_button'),
        ('session_interrupted', 'enable_start_button'),
    )

    def __init__(self, parent):
        Gtk.Toolbar.__init__(
            self,
            icon_size=Gtk.IconSize.LARGE_TOOLBAR,
            orientation=Gtk.Orientation.HORIZONTAL,
            toolbar_style=Gtk.ToolbarStyle.ICONS,
        )

        self.start_button = Gtk.ToolButton(stock_id='gtk-media-play',
                                           tooltip_text=_('Starts the session'))
        self.start_button.connect('clicked', self.on_start_button_clicked)
        self.insert(self.start_button, -1)

        self.interrupt_button = Gtk.ToolButton(stock_id='gtk-media-stop',
                                               tooltip_text=_('Interrupt the session'),
                                               visible=False,
                                               no_show_all=True)
        self.interrupt_button.connect('clicked', self.on_interrupt_button_clicked)
        self.insert(self.interrupt_button, -1)

        self.reset_button = Gtk.ToolButton(stock_id='gtk-refresh',
                                           sensitive=False,
                                           tooltip_text=_('Resets the count '
                                                          'of the pomodoros'))
        self.reset_button.connect('clicked', self.on_reset_button_clicked)
        self.insert(self.reset_button, -1)

        separator = Gtk.SeparatorToolItem(draw=False)
        separator.set_expand(True)
        self.insert(separator, -1)

        self.insert(Appmenu(parent), -1)

        style = self.get_style_context()
        style.add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)

        self.app = Cache.get('GtkApplication')

        self.connect_signals()

    def on_start_button_clicked(self, widget):
        self.app.start()

    def on_interrupt_button_clicked(self, widget):
        self.app.interrupt()

    def on_reset_button_clicked(self, widget):
        self.app.reset()

    def enable_interrupt_button(self, sender=None, **kwargs):
        self.start_button.set_visible(False)

        self.interrupt_button.set_visible(True)

        self.reset_button.set_sensitive(False)

    def enable_start_button(self, sender=None, **kwargs):
        self.start_button.set_visible(True)

        self.interrupt_button.set_visible(False)

        sensitive = bool(kwargs.get('sessions'))
        self.reset_button.set_sensitive(sensitive)

    def disable_reset_button(self, sender=None, **kwargs):
        self.reset_button.set_sensitive(False)


class Appmenu(Gtk.ToolItem):

    def __init__(self, parent):
        Gtk.ToolItem.__init__(self)

        icon = Gtk.Image.new_from_stock('gtk-properties', Gtk.IconSize.LARGE_TOOLBAR)

        appmenu = Gtk.MenuButton(popup=parent.menu)
        appmenu.add(icon)

        self.add(appmenu)


class MainMenu(Gtk.Menu):

    def __init__(self, parent):
        Gtk.Menu.__init__(self, halign=Gtk.Align.CENTER)

        preferences_menu = Gtk.MenuItem(_('Preferences'))
        preferences_menu.connect('activate', self.on_settings_menu_activate, parent)
        self.append(preferences_menu)

        about_menu = Gtk.MenuItem(_('About'))
        about_menu.connect('activate', self.on_about_menu_activate)
        self.append(about_menu)

        self.show_all()

    def on_settings_menu_activate(self, widget, parent):
        dialog = PreferenceDialog(parent)
        dialog.refresh_plugin()
        dialog.run()
        dialog.destroy()

    def on_about_menu_activate(self, widget):
        dialog = AboutDialog(widget.get_ancestor(Gtk.Window))
        dialog.run()
