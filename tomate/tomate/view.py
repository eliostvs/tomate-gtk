from __future__ import unicode_literals

from wiring import Interface


class IView(Interface):

    def run():
        pass

    def quit():
        pass

    def show():
        pass

    def hide():
        pass
