from collections import deque
from functools import reduce
from typing import Any, Callable, List

from gi.repository import GLib, Gtk


class GtkWidgetNotFound(Exception):
    pass


Filter = Callable[[Any], bool]


class Q:
    @staticmethod
    def name(name: str) -> Filter:
        def select(w: Gtk.Widget) -> bool:
            return w.get_name() == name

        return select

    @staticmethod
    def title(title: str) -> Filter:
        def select(widget) -> bool:
            return widget.get_title() == title

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

            if hasattr(widget, "get_children"):
                for child in widget.get_children():
                    queue.append(child)

        raise GtkWidgetNotFound()

    @staticmethod
    def emit(method: str, *args) -> Callable[[Gtk.Widget], None]:
        def effect(w: Gtk.Widget) -> None:
            w.emit(method, *args)

        return effect


class TV:
    @staticmethod
    def map(tree_view: Gtk.TreeView, *fns: Callable[[Any], Any]):
        return reduce(lambda prev, fn: fn(prev), fns, tree_view)

    @staticmethod
    def model(tree_view: Gtk.TreeView) -> Gtk.TreeStore:
        return tree_view.get_model()

    @staticmethod
    def rows(*columns: int) -> Callable[[Gtk.TreeStore], List[Any]]:
        def mapper(tree_store: Gtk.TreeStore) -> List[Any]:
            return [[row[column] for column in columns] for row in tree_store]

        return mapper

    @staticmethod
    def column(fn: Filter) -> Callable[[Gtk.TreeView], List[Gtk.TreeViewColumn]]:
        def select(tree_view: Gtk.TreeView) -> List[Gtk.TreeViewColumn]:
            return [column for column in tree_view.get_columns() if fn(column)][0]

        return select

    @staticmethod
    def cell_renderer(column=0):
        def select(tree_column: Gtk.TreeViewColumn) -> Gtk.CellRenderer:
            return tree_column.get_cells()[column]

        return select


def run_loop_for(seconds: int = 1) -> None:
    GLib.timeout_add_seconds(seconds, Gtk.main_quit)
    Gtk.main()
