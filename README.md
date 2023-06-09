# Tomate

A Pomodoro timer written in Gtk3 and Python for Linux desktops.

## About the technique

The Pomodoro Technique® is a management technique developed by Francesco Cirillo that helps you keep focused.
Read more about it at the [official website](http://pomodorotechnique.com/).

Pomodoro Technique® and Pomodoro™ are registered and filed trademarks owned by Francesco Cirillo.
Tomate is not affiliated by, associated with nor endorsed by Francesco Cirillo.

## Screenshots

![main screen](docs/img/main-screen.png)

![preference duration](docs/img/preference-duration.png)

![preference extension](docs/img/preference-extension.png)

## Installation

### Ubuntu 20.04+

If you have installed the program using the **old ppa repository** uninstall the old version first.
If you use an Ubuntu-based distro, such as Mint, manually set the **RELEASE** variable to the Ubuntu version number, such as 16.04, rather than running the sed script bellow.

```
RELEASE=`sed -n 's/VERSION_ID="\(.*\)"/\1/p' /etc/os-release`
sudo wget -O- http://download.opensuse.org/repositories/home:/eliostvs:/tomate/xUbuntu_$RELEASE/Release.key | sudo apt-key add -
sudo bash -c "echo 'deb http://download.opensuse.org/repositories/home:/eliostvs:/tomate/xUbuntu_$RELEASE/ ./' > /etc/apt/sources.list.d/tomate.list"
sudo apt-get update && sudo apt-get install tomate-gtk
```

### Debian 10+

```bash
RELEASE=`sed -n 's/VERSION_ID="\(.*\)"/\1/p' /etc/os-release`
sudo wget -O- http://download.opensuse.org/repositories/home:/eliostvs:/tomate/Debian_$RELEASE/Release.key | sudo apt-key add -
sudo bash -c "echo 'deb http://download.opensuse.org/repositories/home:/eliostvs:/tomate/Debian_$RELEASE/ ./' > /etc/apt/sources.list.d/tomate.list"
sudo apt-get update && sudo apt-get install tomate-gtk
```

### Opensuse Tumbleweed

```
sudo zypper ar -f http://download.opensuse.org/repositories/home:/eliostvs:/tomate/openSUSE_Tumbleweed/home:eliostvs:tomate.repo
sudo zypper install tomate-gtk
```

### Fedora 36+

```bash
RELEASE=`cat /etc/fedora-release | grep -o '[0-9][0-9]*'`
sudo dnf config-manager --add-repo http://download.opensuse.org/repositories/home:/eliostvs:/tomate/Fedora_$RELEASE/home:eliostvs:tomate.repo
sudo dnf install tomate-gtk
```

### Arch

The packages are available in [aur repository](https://aur.archlinux.org/packages/tomate-gtk/)

## Plugins

### Pre-installed

- [Alarm][alarm-plugin] Play a alarm when the timer end
- [Ticking][ticking-plugin] Play a ticking sound during a work session
- [Notify][notify-plugin] Display notification end the timer start, stop and end
- [Script][script-plugin] Run scripts when the timer start, stop or end
- [Break Screen][breakscreen-plugin] Block all screens during break tim
- [Auto Pause][autopause-plugin] Pause all the playing media when a work session ends

### External

- [Indicator][indicator-plugin] Displays a countdown icon in the systray (uses libappindicator)
- [StatusIcon][statusicon-plugin] Displays a countdown icon in the systray (old method for creating a systray with GNOME)
- [StatusNotifierItem][statusnotifieritem-plugin] Displays a countdown icon in the systray (freedesktop standard for creating a systray)
- [Launcher][launcher-plugin] Shows the timer countdown and the total of sessions in the launcher (ubuntu only)

---

[alarm-plugin]: ./data/plugins/alarm.plugin
[notify-plugin]: ./data/plugins/notify.plugin
[script-plugin]: ./data/plugins/script.plugin
[breakscreen-plugin]: ./data/plugins/breakscreen.plugin
[autopause-plugin]: ./data/plugins/autopause.plugin
[indicator-plugin]: https://github.com/eliostvs/tomate-indicator-plugin
[statusicon-plugin]: https://github.com/eliostvs/tomate-statusicon-plugin
[launcher-plugin]: https://github.com/eliostvs/tomate-launcher-plugin
[statusnotifieritem-plugin]: https://github.com/eliostvs/tomate-statusnotifieritem-plugin
