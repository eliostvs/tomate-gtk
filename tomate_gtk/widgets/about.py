from __future__ import unicode_literals

import tomate_gtk
from gi.repository import GdkPixbuf, Gtk
from tomate.profile import ProfileManager

profile = ProfileManager()


class AboutDialog(Gtk.AboutDialog):

    iconpath = profile.get_icon_path('tomate', 48)

    def __init__(self, parent):
        Gtk.AboutDialog.__init__(
            self,
            comments='Tomate Pomodoro Timer (GTK+ Interface).',
            copyright='2014, Elio Esteves Duarte',
            license='GPL-3',
            license_type=Gtk.License.GPL_3_0,
            logo=GdkPixbuf.Pixbuf.new_from_file(self.iconpath),
            modal=True,
            program_name='Tomate Gtk',
            title='Tomate Gtk',
            transient_for=parent,
            version=tomate_gtk.__version__,
            website='https://github.com/eliostvs/tomate-gtk',
            website_label='Tomate GTK on Github',
        )

        self.set_property('authors', ['Elio Esteves Duarte', ])

        self.connect("response", self.on_dialog_response)

    def on_dialog_response(self, widget, parameter):
        self.destroy()
