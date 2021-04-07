from collections import deque
from functools import reduce
from typing import Any, Callable, List, Optional

from gi.repository import GLib, Gtk


class GtkWidgetNotFound(Exception):
    pass


class Q:
    WidgetFilter = Callable[[Gtk.Widget], bool]

    @staticmethod
    def name(name: str) -> WidgetFilter:
        def select(w: Gtk.Widget) -> bool:
            return w.get_name() == name

        return select

    @staticmethod
    def combine(*fns: WidgetFilter) -> WidgetFilter:
        def select(w: Gtk.Widget) -> bool:
            for fn in fns:
                if not fn(w):
                    return False
                return True

        return select

    @staticmethod
    def select(root: Gtk.Widget, *fns: WidgetFilter) -> Gtk.Widget:
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
        def action(widget: Gtk.Widget) -> None:
            widget.emit(method, *args)

        return action


class TV:
    @staticmethod
    def map(tree_view: Gtk.TreeView, *fns: Callable[[Any], Any]):
        return reduce(lambda prev, fn: fn(prev), fns, tree_view)

    @staticmethod
    def model(tree_view: Gtk.TreeView) -> Gtk.TreeStore:
        return tree_view.get_model()

    @staticmethod
    def row(*columns: int) -> Callable[[Gtk.TreeStore], List[Any]]:
        def mapper(tree_store: Gtk.TreeStore) -> List[Any]:
            return [[row[column] for column in columns] for row in tree_store]

        return mapper

    @staticmethod
    def column(name: str):
        def mapper(tree_view: Gtk.TreeView) -> Callable[[Gtk.TreeView], Optional[Gtk.TreeViewColumn]]:
            columns = [col for col in tree_view.get_columns() if col.get_title() == name]
            return columns[0] if columns else None

        return mapper

    @staticmethod
    def cell_renderer(column=0):
        def select(tree_column: Gtk.TreeView) -> Gtk.CellRenderer:
            return tree_column.get_cells()[column]

        return select


def run_loop_for(seconds: int = 1) -> None:
    GLib.timeout_add_seconds(seconds, Gtk.main_quit)
    Gtk.main()
