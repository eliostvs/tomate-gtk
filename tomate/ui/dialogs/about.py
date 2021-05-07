from gi.repository import GdkPixbuf, Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register


@register.factory("tomate.ui.about", scope=SingletonScope)
class AboutDialog(Gtk.AboutDialog):
    @inject(config="tomate.config")
    def __init__(self, config):
        Gtk.AboutDialog.__init__(
            self,
            comments="Tomate Pomodoro Timer (GTK+ Interface)",
            copyright="2014, Elio Esteves Duarte",
            license="GPL-3",
            license_type=Gtk.License.GPL_3_0,
            logo=GdkPixbuf.Pixbuf.new_from_file(config.icon_path("tomate", 48)),
            modal=True,
            program_name="Tomate Gtk",
            title="Tomate Gtk",
            version="0.13.0",
            website="https://github.com/eliostvs/tomate-gtk",
            website_label="Tomate GTK on Github",
        )

        self.props.authors = ["Elio Esteves Duarte"]
        self.connect("response", lambda widget, _: widget.hide())

    @property
    def widget(self):
        return self
