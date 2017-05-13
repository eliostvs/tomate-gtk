from gi.repository import Gtk

from wiring import SingletonScope
from wiring.scanning import register


@register.factory('view.infobar', scope=SingletonScope)
class InfoBar(Gtk.InfoBar):
    def __init__(self):
        Gtk.InfoBar.__init__(self, show_close_button=True, visible=False, no_show_all=True)
        self.set_default_response(Gtk.ResponseType.CLOSE)

        self.label = Gtk.Label()
        self.get_content_area().add(self.label)
        self.connect('close', lambda widget: self.clear_message_and_hide())

    def show_message(self, message, message_type=Gtk.MessageType.INFO):
        self.label.set_text(message)
        self.set_message_type(message_type)
        self.show_all()

    def clear_message_and_hide(self):
        self.label.set_text('')
        self.hide()

    @property
    def widget(self):
        return self
