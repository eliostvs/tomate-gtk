from __future__ import unicode_literals

import locale
import logging
import time
from locale import gettext as _

from gi.repository import AppIndicator3, GdkPixbuf, Gtk
from tomate.base import ConnectSignalMixin
from tomate.view import IView
from tomate.pomodoro import Task
from tomate.profile import ProfileManagerSingleton
from tomate.signals import (app_exit, change_task, interrupt_session,
                            reset_sessions, start_session, window_visible)
from tomate.utils import format_time_left

from .about import AboutDialog
from .modebutton import ModeButton
from .preference import PreferenceDialog

locale.textdomain('tomate')

logger = logging.getLogger(__name__)

profile = ProfileManagerSingleton.get()


class Window(ConnectSignalMixin,
             IView,
             Gtk.Window):

    signals = (
        ('window_visibility_changed', 'on_window_visibility_changed'),
        ('session_ended', 'show_window'),
    )

    iconpath = profile.get_icon_path('tomate', 22)

    def __init__(self):
        Gtk.Window.__init__(
            self,
            title='Tomate',
            icon=GdkPixbuf.Pixbuf.new_from_file(self.iconpath),
            window_position=Gtk.WindowPosition.CENTER,
            resizable=False
        )

        self.set_size_request(380, 200)
        self.connect('delete-event', self.on_window_delete_event)

        self.menu = Menu(self)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(Toolbar(self), False, False, 0)
        box.pack_start(TimerFrame(), True, True, 0)
        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL),
                       False, False, 8)
        box.pack_start(TaskButtons(), True, True, 0)

        self.add(box)

        self.show_all()

        self.indicator = AppIndicator3.Indicator.new_with_path(
            'tomate',
            'tomate-indicator',
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            profile.get_icon_paths()[0]
        )

        self.indicator.set_menu(self.menu)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        self.connect_signals()

    def show_window(self, sender=None, **kwargs):
        logger.debug('show window')

        window_visible.send(self.__class__, visible=True)

    def hide_window(self):
        logger.debug('Hide window')

        window_visible.send(self.__class__, visible=False)

    def run_window(self):
        Gtk.main()

    def delete_window(self, *args, **kwargs):
        logger.debug('delete window')

        Gtk.main_quit()

    def on_window_delete_event(self, window, event):
        return app_exit.send(self.__class__)

    def on_window_visibility_changed(self, sender=None, **kwargs):
        if kwargs.get('visible', True):
            return self.present_with_time(time.time())

        return self.hide_on_delete()


class TaskButtons(ConnectSignalMixin, ModeButton):

        signals = (
            ('session_started', 'disable_buttons'),
            ('session_interrupted', 'enable_buttons'),
            ('session_ended', 'change_selected'),
            ('session_ended', 'enable_buttons'),
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

            self.connect('mode_changed', self.on_modebutton_mode_changed)

            self.connect_signals()

        def on_modebutton_mode_changed(self, widget, index):
            task = Task.get_by_index(index)

            change_task.send(self.__class__, task=task)

        def change_selected(self, sender=None, **kwargs):
            task = kwargs.get('task', Task.pomodoro)

            logger.debug('Task change %s', task)

            self.set_selected(task.value)

        def disable_buttons(self, sender=None, **kwargs):
            self.set_sensitive(False)

        def enable_buttons(self, sender=None, **kwargs):
            self.set_sensitive(True)


class TimerFrame(ConnectSignalMixin, Gtk.Frame):

        signals = (
            ('session_ended', 'update_session_label'),
            ('sessions_reseted', 'update_session_label'),
            ('session_interrupted', 'update_timer_label'),
            ('task_changed', 'update_timer_label'),
            ('timer_updated', 'update_timer_label'),
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

            self.update_session_label(0)

            self.connect_signals()

        def update_timer_label(self, sender=None, **kwargs):
            time_left = format_time_left(kwargs.get('time_left', 25 * 60))

            markup = '<span font="60">{}</span>'.format(time_left)
            self.timer_label.set_markup(markup)

            logger.debug('timer label update %s', time_left)

        def update_session_label(self, sender=None, **kwargs):
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

        self.connect_signals()

    def on_start_button_clicked(self, widget):
        start_session.send(self.__class__)

    def on_interrupt_button_clicked(self, widget):
        interrupt_session.send(self.__class__)

    def on_reset_button_clicked(self, widget):
        reset_sessions.send(self.__class__)

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


class Menu(ConnectSignalMixin,
           Gtk.Menu):

    signals = (
        ('window_visibility_changed', 'on_window_visibility_changed'),
    )

    def __init__(self, parent):
        Gtk.Menu.__init__(self, halign=Gtk.Align.CENTER)

        self.show_menu = Gtk.MenuItem(_('Show'),
                                      visible=False,
                                      no_show_all=True)
        self.show_menu.connect('activate', self.on_show_menu_activate)

        self.hide_menu = Gtk.MenuItem(_('Hide'))
        self.hide_menu.connect('activate', self.on_hide_menu_activate)

        quit_menu = Gtk.MenuItem(_('Quit'))
        quit_menu.connect('activate', self.on_quit_menu_activate)

        preferences_menu = Gtk.MenuItem(_('Preferences'))
        preferences_menu.connect('activate', self.on_settings_menu_activate, parent)

        about_menu = Gtk.MenuItem(_('About'))
        about_menu.connect('activate', self.on_about_menu_activate)

        quit_menu = Gtk.MenuItem(_('Quit'))
        quit_menu.connect('activate', self.on_quit_menu_activate)

        self.append(self.show_menu)
        self.append(self.hide_menu)
        self.append(preferences_menu)
        self.append(about_menu)
        self.append(Gtk.SeparatorMenuItem())
        self.append(quit_menu)
        self.show_all()

        self.connect_signals()

    def on_show_menu_activate(self, widget):
        window_visible.send(self.__class__, visible=True)

    def on_hide_menu_activate(self, widget):
        window_visible.send(self.__class__, visible=False)

    def on_settings_menu_activate(self, widget, parent):
        dialog = PreferenceDialog(parent)
        dialog.run()
        dialog.destroy()

    def on_about_menu_activate(self, widget):
        dialog = AboutDialog(widget.get_ancestor(Gtk.Window))
        dialog.run()
        dialog.destroy()

    def on_quit_menu_activate(self, widget):
        app_exit.send(self.__class__)

    def on_window_visibility_changed(self, sender=None, **kwargs):
        visible = kwargs.get('visible', True)

        self.hide_menu.set_visible(visible)

        self.show_menu.set_visible(not visible)

        logger.debug('menu visibility changed')
