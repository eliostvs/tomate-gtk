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

Features
--------

Three task timers (pomodoro, short break and long break) and count pomodoro sessions. 
You can extend the program through plugins.
The current plugins are:

- [Alarm plugin (tomate-alarm-plugin)][alarm-plugin]. Plays a sound when the session ends.
- [Notify plugin (tomate-notify-plugin)][notify-plugin]. Shows a notification in the beginning and ending of a session.
- [Indicator plugin (tomate-indicator-plugin)][indicator-plugin]. Shows the timer countdown in the indicator area when window is closed. (Requires libappindicator)
- [Status Icon plugin (tomate-statusicon-plugin)][statusicon-plugin]. Shows the timer countdown in the status area when window is closed.
- [Launcher plugin (tomate-launcher-plugin)][launcher-plugin]. Shows a countdown bar in the Unity launcher and the total of pomodoro sessions. (Ubuntu only)

PLugin installation
-------------------

1. Install the plugin. (ex. `apt-get install tomate-indicator-plugin`) 
2. Click in the *Appmenu* > *Preferences* > *Extensions* and enable the plugin.

Bugs and Suggetions
-------------------

Bugs and suggestions should be reported [here][bugs].

Changelog
---------

## v0.6.0

- Using py.test
- Add view menu

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
