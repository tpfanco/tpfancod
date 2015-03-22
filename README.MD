# Warning

The code in this repository is not yet ready for productive use!
Use it on your own risk!

# Tpfanco daemon (tpfancod)

tpfancod controls the system fan of ThinkPad notebooks based on specified 
temperature profiles. Seperate trigger points can be configured for every
temperature sensor in the notebook.

tpfancod is written entirely in Python and licensed under the GNU GPL version 3.

# Requirements

* Python 2.7
* DBus with bindings for Python
* python-dmidecode module
* thinkpad_acpi kernel module loaded with fan_control=1 to enable fan control.

# Installation

* If you use a distribution with systemd (e.g Fedora), run
	`sudo make install-systemd` and `sudo systemctl enable tpfand`.
	Reboot your system to finish the install process.

*	If you use a distribution with sysvinit (e.g Debian or Ubuntu), run
	`sudo make install-sysvinit`. Reboot your system to finish the install process.

*	You can uninstall tpfancod by running `sudo make uninstall`.

# Configuration

* The configuration file is `/etc/tpfancod/settings.conf`.
	After manual changes to this configuration file tpfancod must
	be restarted.

* Currently tpfanco-admin doesn't work with tpfancod


