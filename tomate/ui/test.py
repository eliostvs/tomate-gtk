from functools import reduce
from typing import Callable, Optional, Any, List

from gi.repository import Gtk, GLib


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
    def select(root: Gtk.Widget, *fns: WidgetFilter) -> Optional[Gtk.Widget]:
        fn = Q.combine(*fns)

        queue = [root]
        while queue:
            widget = queue.pop(0)
            if fn(widget):
                return widget

            if hasattr(widget, "get_children"):
                for child in widget.get_children():
                    queue.append(child)

    @staticmethod
    def emit(method: str, *args) -> Callable[[Gtk.Widget], None]:
        def action(widget: Gtk.Widget) -> None:
            widget.emit(method, *args)

        return action


class T:
    @staticmethod
    def query(tree_view: Gtk.TreeView, *fns):
        return reduce(lambda prev, fn: fn(prev), fns, tree_view)

    @staticmethod
    def model(tree_view: Gtk.TreeView) -> Gtk.TreeStore:
        return tree_view.get_model()

    @staticmethod
    def items_columns(*columns: int) -> Callable[[Gtk.TreeView], Optional[List[Any]]]:
        def transform(tree_store: Gtk.TreeStore) -> Optional[List[Any]]:
            return [[row[column] for column in columns] for row in tree_store]

        return transform

    @staticmethod
    def column(name: str):
        def transform(tree_view: Gtk.TreeView):
            columns = [col for col in tree_view.get_columns() if col.get_title() == name]
            if columns:
                return columns[0]
            return []

        return transform

    @staticmethod
    def cell(position=0):
        def select(tree_column: Gtk.TreeView) -> Gtk.CellRenderer:
            return tree_column.get_cells()[position]

        return select


def run_loop_for(seconds: int = 1) -> None:
    GLib.timeout_add_seconds(seconds, Gtk.main_quit)
    Gtk.main()
