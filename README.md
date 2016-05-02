Tomate GTK
==========

A open source timer for the Pomodoro Technique®.

About the technique
-------------------

The Pomodoro Technique® is a management technique developed by Francesco Cirillo that helps you keep focused.
Read more about it at the [official website](http://pomodorotechnique.com/).

Pomodoro Technique® and Pomodoro™ are registered and filed trademarks owned by Francesco Cirillo.
Tomate is not affiliated by, associated with nor endorsed by Francesco Cirillo.

Installation
------------

### Ubuntu 14.04+

If you have installed the program using the **old ppa repository** uninstall the old version first.

    RELEASE=`sed -n 's/VERSION_ID="\(.*\)"/\1/p' /etc/os-release`
    sudo wget -O- http://download.opensuse.org/repositories/home:/eliostvs:/tomate/xUbuntu_$RELEASE/Release.key | sudo apt-key add -
    sudo bash -c "echo 'deb http://download.opensuse.org/repositories/home:/eliostvs:/tomate/xUbuntu_$RELEASE/ ./' > /etc/apt/sources.list.d/tomate.list"
    sudo apt-get update && sudo apt-get install tomate-gtk

### Debian 8+

    RELEASE=`sed -n 's/VERSION_ID="\(.*\)"/\1\.0/p' /etc/os-release`
    sudo wget -O- http://download.opensuse.org/repositories/home:/eliostvs:/tomate/Debian_$RELEASE/Release.key | sudo apt-key add -
    sudo bash -c "echo 'deb http://download.opensuse.org/repositories/home:/eliostvs:/tomate/Debian_$RELEASE/ ./' > /etc/apt/sources.list.d/tomate.list"
    sudo apt-get update && sudo apt-get install tomate-gtk

### Opensuse 13.2+

    RELEASE=`cat /etc/SuSE-release | sed -n "s/VERSION = \(.*\)$/\1/p"` # If you use tumbleweed release is Tumbleweed
    sudo zypper ar -f http://download.opensuse.org/repositories/home:/eliostvs:/tomate/openSUSE_$RELEASE/home:eliostvs:tomate.repo
    sudo zypper install tomate-gtk

### Fedora 22+

    RELEASE=`cat /etc/fedora-release | grep -o '[0-9][0-9]*'`
    sudo yum-config-manager --add-repo http://download.opensuse.org/repositories/home:/eliostvs:/tomate/Fedora_$RELEASE/home:eliostvs:tomate.repo
    sudo yum install tomate-gtk

or

    RELEASE=`cat /etc/fedora-release | grep -o '[0-9][0-9]*'
    sudo dnf config-manager --add-repo http://download.opensuse.org/repositories/home:/eliostvs:/tomate/Fedora_$RELEASE/home:eliostvs:tomate.repo
    sudo dnf install tomate-gtk

### Arch

    yaourt -S tomate-gtk

Plugins
-------

- [Alarm plugin (tomate-alarm-plugin)][alarm-plugin] Plays a sound when the timer ends.
- [Notify plugin (tomate-notify-plugin)][notify-plugin] Shows a OSD notification.
- [Indicator plugin (tomate-indicator-plugin)][indicator-plugin] Shows the timer countdown in the indicator area (requires libappindicator).
- [Status Icon plugin (tomate-statusicon-plugin)][statusicon-plugin] Shows the timer countdown in the status area.
- [Launcher plugin (tomate-launcher-plugin)][launcher-plugin] Shows the timer countdown and the total of sessions in the launcher (ubuntu only).

All plugins are in the repositories.

Bugs and Suggetions
-------------------

Bugs and suggestions should be reported [here][bugs].

Change Logs
-----------

## v0.6.0

- Using py.test
- Add trayicon menu widget

### v0.5.0

- Remove linux package metadata
- Fix Gtk warnings

### v0.4.0

- Using the new event system
- Python 2/3 compatible (only for Ubuntu/Debian/Arch)
- Remove appindicator3 dependency

License
-------

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License version 3, as published
by the Free Software Foundation.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranties of
MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program.  If not, see <http://www.gnu.org/licenses/>.

[alarm-plugin]: https://github.com/eliostvs/tomate-alarm-plugin
[notify-plugin]: https://github.com/eliostvs/tomate-notify-plugin
[indicator-plugin]: https://github.com/eliostvs/tomate-indicator-plugin
[statusicon-plugin]: https://github.com/eliostvs/tomate-statusicon-plugin
[launcher-plugin]: https://github.com/eliostvs/tomate-launcher-plugin
[bugs]: https://github.com/eliostvs/tomate-gtk/issues
