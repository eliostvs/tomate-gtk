from gi.repository import GObject, Gtk


class ModeButtonItem(Gtk.ToggleButton):
    def __init__(self, index):
        Gtk.ToggleButton.__init__(self, can_focus=False)

        self.index = index


class ModeButton(Gtk.Box):
    __gsignals__ = {
        'mode_changed': (GObject.SIGNAL_RUN_FIRST, None, (int,))
    }

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self, **kwargs)

        self.__itens = {}
        self.__selected = None

        style = self.get_style_context()
        style.add_class(Gtk.STYLE_CLASS_LINKED)
        style.add_class('raised')

    def get_selected(self):
        return self.__selected

    def append_text(self, text):
        button = ModeButtonItem(len(self.__itens))
        button.add(Gtk.Label.new(text))
        button.connect('button_press_event', self.on_button_press_event)
        button.show_all()

        self.__itens[button.index] = button
        self.add(button)
        self.set_selected(button.index)

    def on_button_press_event(self, widget, event=None):
        return self.set_selected(widget.index)

    def set_selected(self, index):
        if index in self.__itens.keys():
            try:
                old_item = self.__itens[self.__selected]
                old_item.set_active(False)

            except KeyError:
                pass

            new_item = self.__itens[index]
            new_item.set_active(True)

            self.__selected = index

            self.emit('mode_changed', self.__selected)

            return True
