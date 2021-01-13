from typing import Dict, Any

from gi.repository import GObject, Gtk


class ModeButtonItem(Gtk.ToggleButton):
    def __init__(self, index: int, **props: Dict[str, Any]):
        Gtk.ToggleButton.__init__(self, can_focus=False, **props)
        self.index = index


class ModeButton(Gtk.Box):
    __gsignals__ = {"mode_changed": (GObject.SignalFlags.RUN_FIRST, None, (int,))}

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self, **kwargs)

        self.__items = {}
        self.__selected = None

        style = self.get_style_context()
        style.add_class(Gtk.STYLE_CLASS_LINKED)
        style.add_class("raised")

    def get_selected(self):
        return self.__selected

    def append_text(self, text: str, **props: Dict[str, Any]):
        button = ModeButtonItem(len(self.__items), **props)
        button.add(Gtk.Label.new(text))
        button.connect("button_press_event", self.on_button_press_event)
        button.show_all()

        self.__items[button.index] = button
        self.add(button)
        self.set_selected(button.index)

    def on_button_press_event(self, widget, event=None):
        return self.set_selected(widget.index)

    def set_selected(self, index):
        if self.get_sensitive() and index in self.__items.keys():
            try:
                old_item = self.__items[self.__selected]
                old_item.set_active(False)
            except KeyError:
                pass

            new_item = self.__items[index]
            new_item.set_active(True)

            self.__selected = index

            self.emit("mode_changed", self.__selected)

            return True
