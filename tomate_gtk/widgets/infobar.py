from __future__ import unicode_literals

from gi.repository import Gtk, GLib

from wiring import Interface, implements, Module, SingletonScope


class Infobar(Gtk.InfoBar):
    def __init__(self):
        Gtk.InfoBar.__init__(self, no_show_all=True)
        style = self.get_style_context()
        style.add_class(Gtk.STYLE_CLASS_INFO)
        self.label = Gtk.Label()
        self.container.add(self.label)

        self.connect('close', self.on_infobar_close)
        self.connect('response', self.on_infobar_close)
        self.callback = None

    def add_callback_with_message(self, button_text, callback, message, message_type=Gtk.MessageType.INFO, timeout=5):
        self.show_message(message, message_type, timeout=0)
        self.add_callback(button_text, callback)
        self.hide_after(timeout)

    def add_callback(self, button_text, callback):
        self.add_button(button_text, Gtk.ResponseType.NONE)
        self.set_show_close_button(False)
        self.callback = callback

    def show_message(self, message, message_type=Gtk.MessageType.INFO, timeout=3):
        self.label.set_label(message)
        self.set_message_type(message_type)
        self.set_show_close_button(True)
        self.hide_after(timeout)

    @property
    def container(self):
        return self.get_content_area()

    def hide_after(self, timeout=3):
        if timeout:
            GLib.timeout_add(timeout * 1000, self.on_infobar_close)

    def on_infobar_close(self, widget=None, event=None):
        self.hide()

        if self.callback:
            self.callback()
            self.callback = None

    @property
    def widget(self):
        return self


class InfobarModule(Module):
    factories = {
        'view.infobar': (Infobar, SingletonScope),
    }
