DESTDIR=/

all: man

man: tpfancod.8

tpfancod.8: man/tpfancod.pod
	pod2man --utf8 --section=8 --release="Version `cat src/tpfancod.py | grep \"version = \" | grep -o '[0-9]*\.[0-9]*\.[0-9]*'`" --center "" man/tpfancod.pod > tpfancod.8

clean:
	rm -f tpfancod.8
	rm -f src/tpfancod/*.pyc

sysvinit:
	install -d $(DESTDIR)/etc/init.d
	install -m 755 etc/init.d/tpfancod $(DESTDIR)/etc/init.d/
	install -d $(DESTDIR)/etc/acpi/suspend.d
	install -m 755 etc/acpi/suspend.d/acpi-stop.sh $(DESTDIR)/etc/acpi/suspend.d/09-tpfancod-stop.sh
	install -d $(DESTDIR)/etc/acpi/resume.d
	install -m 755 etc/acpi/resume.d/acpi-start.sh $(DESTDIR)/etc/acpi/resume.d/91-tpfancod-start.sh
	echo Installation complete.
	echo You still need to create links to the init script.

systemd:
	install -d $(DESTDIR)/etc/systemd/system
	install -m 755 etc/systemd/system/tpfancod.service $(DESTDIR)/etc/systemd/system/
	install -d $(DESTDIR)/usr/lib/systemd/system-sleep
	install -m 755 usr/lib/systemd/system-sleep/tpfancod-notify.sh $(DESTDIR)/usr/lib/systemd/system-sleep
	echo Installation complete.
	echo You still need to run "sudo systemctl enable tpfancod" to enable tpfancod service

standard:
	install -d $(DESTDIR)/usr/lib/python2.7/site-packages/tpfancod
	install -m 644 src/tpfancod/* $(DESTDIR)/usr/lib/python2.7/site-packages/tpfancod
	install -d $(DESTDIR)/etc/tpfancod/
	install -d $(DESTDIR)/etc/dbus-1/system.d/
	install -m 644 etc/dbus-1/system.d/tpfancod.conf $(DESTDIR)/etc/dbus-1/system.d/tpfancod.conf
	install -d $(DESTDIR)/usr/share/polkit-1
	install -d $(DESTDIR)/usr/share/polkit-1/actions
	install -m 644 share/polkit-1/actions/org.tpfanco.tpfancod.policy $(DESTDIR)/usr/share/polkit-1/actions/org.tpfanco.tpfancod.policy
	install -d $(DESTDIR)/usr/sbin
	install -m 755 src/tpfancod.py $(DESTDIR)/usr/sbin/tpfancod
	install -d $(DESTDIR)/etc/modprobe.d
	install -m 644 etc/modprobe.d/tpfancod.conf $(DESTDIR)/etc/modprobe.d/

install-sysvinit: all standard sysvinit

install-systemd: all standard systemd

uninstall:
	rm -rf $(DESTDIR)/usr/lib/python2.7/site-packages/tpfancod
	rm -f $(DESTDIR)/usr/sbin/tpfancod
	rm -f $(DESTDIR)/etc/init.d/tpfancod
	rm -f $(DESTDIR)/etc/systemd/system/tpfancod.service
	rm -f $(DESTDIR)/usr/lib/systemd/system-sleep/tpfancod-notify.sh
	rm -f $(DESTDIR)/etc/dbus-1/system.d/tpfancod.conf
	rm -f $(DESTDIR)/usr/share/polkit-1/actions/org.tpfanco.tpfancod.policy
	rm -f $(DESTDIR)/etc/acpi/suspend.d/09-tpfancod-stop.sh
	rm -f $(DESTDIR)/etc/acpi/resume.d/91-tpfancod-start.sh
	rm -f $(DESTDIR)/etc/modprobe.d/tpfancod.conf



