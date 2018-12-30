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

### Ubuntu 16.04+

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

### Opensuse Tumbleweed

    sudo zypper ar -f http://download.opensuse.org/repositories/home:/eliostvs:/tomate/openSUSE_Tumbleweed/home:eliostvs:tomate.repo
    sudo zypper install tomate-gtk

### Fedora 24+

    RELEASE=`cat /etc/fedora-release | grep -o '[0-9][0-9]*'`
    sudo dnf config-manager --add-repo http://download.opensuse.org/repositories/home:/eliostvs:/tomate/Fedora_$RELEASE/home:eliostvs:tomate.repo
    sudo dnf install tomate-gtk

### Arch

    pacaur -S tomate-gtk

Plugins
-------

All plugins are in the repositories and need to be installed separately.
For example `sudo apt-get install tomate-indicator-plugin` will install the indicator plugin under Debian and Ubuntu.

- [Alarm plugin (tomate-alarm-plugin)][alarm-plugin] Plays a sound when the timer ends.
- [Notify plugin (tomate-notify-plugin)][notify-plugin] Shows a OSD notification.
- [Indicator plugin (tomate-indicator-plugin)][indicator-plugin] Shows the timer countdown in the indicator area **when the timer is running** (requires libappindicator).
- [Status Icon plugin (tomate-statusicon-plugin)][statusicon-plugin] Shows the timer countdown in the status area **when the timer is running**.
- [Launcher plugin (tomate-launcher-plugin)][launcher-plugin] Shows the timer countdown and the total of sessions in the launcher (ubuntu only).
- [Exec plugin (tomate-exec-plugin)][exec-plugin] Run commands when the timer starts, stops or finishes.

Bugs and Suggestions
-------------------

Bugs and suggestions should be reported [here][bugs].

Changelog
---------

### 0.9.0

#### Changed

- Change UI to use a headerbar widget instead of a toolbar
- The Task enum was renamed to Sessions

#### Removed

- Show notifications in then main widget (**show\_message view interface**)

### 0.8.0

#### Added

- Show notifications in the main widget (**show\_message** view interface)

#### Fixed

- Reopen from command line

#### Changed

- Arch install instructions

### 0.7.0

- Using wiring.scanning
- Add plugin settings
- Python 3 only

### 0.6.0

- Using py.test
- Add menu widget

### 0.5.0

- Remove linux package metadata
- Fix Gtk warnings

### 0.4.0

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
[exec-plugin]: https://github.com/eliostvs/tomate-exec-plugin
[bugs]: https://github.com/eliostvs/tomate-gtk/issues
