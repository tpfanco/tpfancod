DESTDIR=/

all: man

man: tpfand.8

tpfand.8: man/tpfand.pod
	pod2man --section=8 --release=Version\ `cat src/tpfand/build.py | grep "version = " | sed  -e "s/version = \"\(.*\)\"/\1/"` --center "" man/tpfand.pod > tpfand.8

clean:
	rm -f tpfand.8
	rm -f src/tpfand/*.pyc

sysvinit:
	install -d $(DESTDIR)/usr/share/pyshared/tpfand
	install -m 644 src/tpfand/* $(DESTDIR)/usr/share/pyshared/tpfand
	install -d $(DESTDIR)/etc/init.d
	install -m 755 etc/init.d/tpfand $(DESTDIR)/etc/init.d/
	install -d $(DESTDIR)/etc/acpi/suspend.d
	install -m 755 etc/acpi/suspend.d/acpi-stop.sh $(DESTDIR)/etc/acpi/suspend.d/09-tpfand-stop.sh
	install -d $(DESTDIR)/etc/acpi/resume.d
	install -m 755 etc/acpi/resume.d/acpi-start.sh $(DESTDIR)/etc/acpi/resume.d/91-tpfand-start.sh
	echo Installation complete.
	echo You still need to create links to the init script.

systemd:
	install -d $(DESTDIR)/usr/lib/python2.7/site-packages/tpfand
	install -m 644 src/tpfand/* $(DESTDIR)/usr/lib/python2.7/site-packages/tpfand
	install -d $(DESTDIR)/etc/systemd/system
	install -m 755 etc/systemd/system/tpfand.service $(DESTDIR)/etc/systemd/system/
	install -d $(DESTDIR)/usr/lib/systemd/system-sleep
	install -m 755 usr/lib/systemd/system-sleep/tpfand-notify.sh $(DESTDIR)/usr/lib/systemd/system-sleep
	echo Installation complete.
	echo You still need to run "sudo systemctl enable tpfand" to enable tpfand service

standard:
	install -d $(DESTDIR)/usr/share/tpfand/
	install -d $(DESTDIR)/usr/share/tpfand/models
	install -d $(DESTDIR)/usr/share/tpfand/models/by-id
	install -d $(DESTDIR)/usr/share/tpfand/models/by-name
	install -m 644 share/models/generic $(DESTDIR)/usr/share/tpfand/models
	install -d $(DESTDIR)/etc/dbus-1/system.d/
#	install -m 644 etc/dbus-1/system.d/org.tpfanco.tpfand.conf $(DESTDIR)/etc/dbus-1/system.d/org.tpfanco.tpfand.conf
	install -m 644 etc/dbus-1/system.d/tpfand.conf $(DESTDIR)/etc/dbus-1/system.d/tpfand.conf
#	install -d $(DESTDIR)/usr/share/polkit-1
#	install -d $(DESTDIR)/usr/share/polkit-1/actions
#	install -m 644 share/polkit-1/actions/org.tpfanco.settings.policy $(DESTDIR)/usr/share/polkit-1/actions/org.tpfanco.settings.policy
	install -d $(DESTDIR)/usr/sbin
	install -m 755 src/tpfand.py $(DESTDIR)/usr/sbin/tpfand
	install -d $(DESTDIR)/etc/modprobe.d
	install -m 644 etc/modprobe.d/tpfand.conf $(DESTDIR)/etc/modprobe.d/

install-sysvinit: all standard sysvinit

install-systemd: all standard systemd

uninstall:
	rm -rf $(DESTDIR)/usr/share/pyshared/tpfand
	rm -rf $(DESTDIR)/usr/lib/python2.7/site-packages/tpfand
	rm -rf $(DESTDIR)/usr/share/tpfand/
	rm -f $(DESTDIR)/usr/sbin/tpfand
	rm -f $(DESTDIR)/etc/init.d/tpfand
	rm -f $(DESTDIR)/etc/systemd/system/tpfand.service
	rm -f $(DESTDIR)/usr/lib/systemd/system-sleep/tpfand-notify.sh
#	rm -f $(DESTDIR)/etc/dbus-1/system.d/org.tpfanco.tpfand.conf
	rm -f $(DESTDIR)/etc/dbus-1/system.d/tpfand.conf
#	rm -f $(DESTDIR)/usr/share/polkit-1/actions/org.tpfanco.settings.policy
	rm -f $(DESTDIR)/etc/acpi/suspend.d/09-tpfand-stop.sh
	rm -f $(DESTDIR)/etc/acpi/resume.d/91-tpfand-start.sh
	rm -f $(DESTDIR)/etc/modprobe.d/tpfand.conf



