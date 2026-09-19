from collections.abc import Callable
from locale import gettext as _
from typing import Protocol

from gi.repository import Gtk

from tomate.pomodoro.event import Bus, Event, Events, Subscriber, on


class TraySystem(Protocol):
    """An activated tray implementation that can show or hide its window."""

    def show(self) -> object: ...

    def hide(self) -> object: ...


class SysTray:
    def __init__(self) -> None:
        self._systems: list[TraySystem] = []

    @property
    def available(self) -> bool:
        return bool(self._systems)

    def register(self, system: TraySystem) -> None:
        if not any(registered is system for registered in self._systems):
            self._systems.append(system)

    def unregister(self, system: TraySystem) -> None:
        """Stop tracking an implementation, if that exact object is active."""

        for index, registered in enumerate(self._systems):
            if registered is system:
                del self._systems[index]
                return


class Menu(Subscriber):
    def __init__(self, bus: Bus, window) -> None:
        self.widget, self.show_item, self.hide_item = self._create_menu(window)
        self.connect(bus)

    def _create_menu(self, window) -> tuple[Gtk.Menu, Gtk.MenuItem, Gtk.MenuItem]:
        menu = Gtk.Menu(halign=Gtk.Align.CENTER)
        show_item = self._create_menu_item("Show", lambda _: window.show(), visible=False, no_show_all=True)
        hide_item = self._create_menu_item("Hide", lambda _: window.hide(), visible=True)
        menu.add(show_item)
        menu.add(hide_item)
        menu.show_all()
        return menu, show_item, hide_item

    def _create_menu_item(self, label: str, activate: Callable[[Gtk.MenuItem], None], **props) -> Gtk.MenuItem:
        menu_item = Gtk.MenuItem.new_with_label(_(label))
        menu_item.set_properties(**props)
        menu_item.connect("activate", activate)
        return menu_item

    @on(Events.WINDOW_SHOW)
    def _on_window_show(self, _event: Event[None]):
        self.hide_item.props.visible = True
        self.show_item.props.visible = False

    @on(Events.WINDOW_HIDE)
    def _on_window_hide(self, _event: Event[None]):
        self.hide_item.props.visible = False
        self.show_item.props.visible = True
