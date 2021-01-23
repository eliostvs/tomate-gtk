### [Unreleased]

#### Added

- Keyboard shortcuts to change the type of the session: pomodoro (control + 1), short break (control + 2) and long break (control + 3)

#### Changed

- Join python-tomate and tomate-gtk projects
- Move enums to package init module
- Change tomate.events.setting event namespace to tomate.events.config
- Change session payload fields
- Change Events.Setting to Events.Config
- Trigger State.finished and State.changed in the end of a session

### 0.11.0

#### Added

- Keyboard shortcuts to start (control + s), stop (control + p) and reset (control + r) sessions

### 0.10.0

#### Changed

- The timer, session and settings now emit a payload object instead of a dictionary

### 0.9.2

#### Fixed

- Timer countdown blinking

### 0.9.1

#### Changed

- Arch linux installation instructions

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