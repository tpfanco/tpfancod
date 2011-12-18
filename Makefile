DESTDIR=/

all: man

man: tpfand.8

tpfand.8: man/tpfand.pod
	pod2man --section=8 --release=Version\ `cat src/tpfand/build.py | grep "version = " | sed  -e "s/version = \"\(.*\)\"/\1/"` --center "" man/tpfand.pod > tpfand.8

clean:
	rm -f tpfand.8
	rm -f src/tpfand/*.pyc

install: all
	install -d $(DESTDIR)/usr/share/pyshared/tpfand
	install -m 644 src/tpfand/* $(DESTDIR)/usr/share/pyshared/tpfand
	install -d $(DESTDIR)/usr/share/tpfand/
	install -d $(DESTDIR)/usr/share/tpfand/models
	install -d $(DESTDIR)/usr/share/tpfand/models/by-id
	install -d $(DESTDIR)/usr/share/tpfand/models/by-name
	install -m 644 share/models/generic $(DESTDIR)/usr/share/tpfand/models
	install -d $(DESTDIR)/etc/dbus-1/system.d/
	install -m 644 etc/dbus-1/system.d/tpfand.conf $(DESTDIR)/etc/dbus-1/system.d/tpfand.conf
	install -d $(DESTDIR)/usr/sbin
	install -m 755 wrappers/tpfand $(DESTDIR)/usr/sbin/
	install -d $(DESTDIR)/etc/init.d
	install -m 755 etc/init.d/* $(DESTDIR)/etc/init.d/
	install -d $(DESTDIR)/etc/acpi/suspend.d
	install -m 755 etc/acpi/suspend.d/acpi-stop.sh $(DESTDIR)/etc/acpi/suspend.d/09-tpfand-stop.sh
	install -d $(DESTDIR)/etc/acpi/resume.d
	install -m 755 etc/acpi/resume.d/acpi-start.sh $(DESTDIR)/etc/acpi/resume.d/91-tpfand-start.sh
	install -d $(DESTDIR)/etc/modprobe.d
	install -m 644 etc/modprobe.d/tpfand.conf $(DESTDIR)/etc/modprobe.d/
	if [ ! -e $(DESTDIR)/etc/tpfand.conf ] ; then install -m 644 etc/tpfand.conf $(DESTDIR)/etc/tpfand.conf ; fi
	echo Installation complete.
	echo You still need to create links to the init script. 

uninstall:
	rm -rf $(DESTDIR)/usr/share/pyshared/tpfand
	rm -rf $(DESTDIR)/usr/share/tpfand/
	rm -f $(DESTDIR)/usr/sbin/tpfand
	rm -f $(DESTDIR)/etc/init.d/tpfand
	rm -f $(DESTDIR)/etc/dbus-1/system.d/tpfand.conf
	rm -f $(DESTDIR)/etc/acpi/suspend.d/09-tpfand-stop.sh
	rm -f $(DESTDIR)/etc/acpi/resume.d/91-tpfand-start.sh
	rm -f $(DESTDIR)/etc/modprobe.d/tpfand.conf
	rm -f $(DESTDIR)/etc/tpfand.conf



