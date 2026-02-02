import time
from collections import deque
from functools import reduce
from typing import Any, Callable, List, Optional

from gi.repository import GLib, Gtk

from tomate.pomodoro import SessionPayload, SessionType
from tomate.ui import Shortcut, ShortcutEngine


def active_shortcut(shortcut_engine: ShortcutEngine, shortcut: Shortcut, window: Optional[Gtk.Window] = None) -> bool:
    if window is None:
        app = Gtk.Application(application_id="com.github.Tomate.Test")
        window = Gtk.ApplicationWindow(application=app)

    shortcut_engine.init(window)
    action_name = shortcut_engine.action_name(shortcut)
    if not action_name:
        return False
    return window.activate_action(action_name, None)


def create_session_payload(**kwargs) -> SessionPayload:
    defaults = {
        "duration": 25 * 60,
        "pomodoros": 0,
        "type": SessionType.POMODORO,
    }
    defaults.update(kwargs)
    return SessionPayload(**defaults)


def run_loop_for(seconds: int = 1) -> None:
    end = time.time() + seconds
    context = GLib.MainContext.default()
    while time.time() < end:
        context.iteration(False)


def refresh_gui(delay: int = 0) -> None:
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(False)
    time.sleep(delay)


class GtkWidgetNotFound(Exception):
    pass


Filter = Callable[[Any], bool]


class Q:
    @staticmethod
    def props(name: str, value: Any) -> Filter:
        def select(w: Gtk.Widget) -> bool:
            if hasattr(w.props, name):
                return getattr(w.props, name) == value
            return False

        return select

    @staticmethod
    def combine(*fns: Filter) -> Filter:
        def select(w: Gtk.Widget) -> bool:
            for fn in fns:
                if not fn(w):
                    return False
                return True

        return select

    @staticmethod
    def select(root: Gtk.Widget, *fns: Filter) -> Gtk.Widget:
        fn = Q.combine(*fns)
        queue = deque([root])
        while queue:
            widget = queue.popleft()
            if fn(widget):
                return widget

            if hasattr(widget, "get_first_child"):
                child = widget.get_first_child()
                while child is not None:
                    queue.append(child)
                    child = child.get_next_sibling()
            elif hasattr(widget, "get_child"):
                child = widget.get_child()
                if child is not None:
                    queue.append(child)
            elif hasattr(widget, "get_children"):
                for child in widget.get_children():
                    queue.append(child)

        raise GtkWidgetNotFound()

    @staticmethod
    def emit(method: str, *args) -> Callable[[Gtk.Widget], None]:
        def effect(w: Gtk.Widget) -> None:
            w.emit(method, *args)

        return effect

    @staticmethod
    def map(widget: Gtk.Widget, *fns: Callable[[Any], Any]):
        return reduce(lambda prev, fn: fn(prev), fns, widget)


class TV:
    @staticmethod
    def model(tree_view: Gtk.TreeView) -> Gtk.TreeStore:
        return tree_view.get_model()

    @staticmethod
    def column(fn: Filter) -> Callable[[Gtk.TreeView], List[Gtk.TreeViewColumn]]:
        def select(tree_view: Gtk.TreeView) -> List[Gtk.TreeViewColumn]:
            return [column for column in tree_view.get_columns() if fn(column)][0]

        return select

    @staticmethod
    def cell_renderer(position: int) -> Callable[[Gtk.TreeViewColumn], Gtk.CellRenderer]:
        def select(tree_column: Gtk.TreeViewColumn) -> Gtk.CellRenderer:
            return tree_column.get_cells()[position]

        return select
