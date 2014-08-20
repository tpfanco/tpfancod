#! /usr/bin/python2.7
# -*- coding: utf8 -*-
#
# tpfanco - controls the fan-speed of IBM/Lenovo ThinkPad Notebooks
# Copyright (C) 2011-2014 Vladyslav Shtabovenko
# Copyright (C) 2007-2009 Sebastian Urban
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os.path
import signal
import sys
import argparse
import dbus.mainloop.glib
import gobject

from tpfand import build, settings, control
if not ('/usr/share/pyshared' in sys.path):
    sys.path.append('/usr/share/pyshared')
if not ('/usr/lib/python2.7/site-packages' in sys.path):
    sys.path.append('/usr/lib/python2.7/site-packages')


class Tpfand(object):

    """main tpfand process"""

    debug = False
    quiet = False
    noibmthermal = False

    def __init__(self):
        self.parse_command_line_args()
        self.start_fan_control()

    def parse_command_line_args(self):
        """evaluate command line arguments"""

        parser = argparse.ArgumentParser()

        parser.add_argument('-d', '--debug', help='enable debugging output',
                            action='store_true')
        parser.add_argument('-n', '--noibmthermal', help='use hwmon sensors even if /proc/acpi/ibm/thermal is present',
                            action='store_true')
        parser.add_argument('-q', '--quiet', help='minimize console output',
                            action='store_true')
        args = parser.parse_args()

        self.debug = args.debug
        self.quiet = args.quiet
        self.noibmthermal = args.noibmthermal

    def start_fan_control(self):
        """daemon start function"""

        if not self.quiet:
            print 'tpfand ' + build.version + ' - Copyright (C) 2011-2012 Vladyslav Shtabovenko'
            print 'Copyright (C) 2007-2008 Sebastian Urban'
            print 'This program comes with ABSOLUTELY NO WARRANTY'
            print
            print 'WARNING: THIS PROGRAM MAY DAMAGE YOUR COMPUTER.'
            print '         PROCEED ONLY IF YOU KNOW HOW TO MONITOR SYSTEM TEMPERATURE.'
            print

        if self.debug:
            print 'Running in debug mode'

        if not self.is_system_suitable():
            print 'Fatal error: unable to set fanspeed, enable watchdog or read temperature'
            print '             Please make sure you are root and a recent'
            print '             thinkpad_acpi module is loaded with fan_control=1'
            print '             If thinkpad_acpi is already loaded, check that'
            print '             /proc/acpi/ibm/thermal exists. Thinkpad models'
            print '             that doesn\'t have this file are currently unsupported'
            exit(1)

        if os.path.isfile(build.pid_path):
            print 'Fatal error: already running or ' + build.pid_path + ' left behind'
            exit(1)

        # go into daemon mode
        self.daemonize()

    def is_system_suitable(self):
        """returns True iff fan speed setting, watchdog and thermal reading is supported by kernel and
           we have write permissions"""
        try:
            fanfile = open(build.ibm_fan, 'w')
            fanfile.write('level auto')
            fanfile.flush()
            fanfile.close()
            fanfile = open(build.ibm_fan, 'w')
            fanfile.write('watchdog 5')
            fanfile.flush()
            fanfile.close()

            tempfile = open(build.ibm_thermal, 'r')
            tempfile.readline()
            tempfile.close()
            return True
        except IOError:
            return False

    def daemonize(self):
        """turns the current process into a daemon"""

        if not self.debug:  # don't go into daemon mode if debug mode is active
            """go into daemon mode"""
            # from: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
            # do the UNIX double-fork magic, see Stevens' "Advanced
            # Programming in the UNIX Environment" for details (ISBN
            # 0201563177)
            try:
                pid = os.fork()
                if pid > 0:  # exit first parent
                    sys.exit(0)
            except OSError, e:
                print >>sys.stderr, 'fork #1 failed: %d (%s)' % (
                    e.errno, e.strerror)
                sys.exit(1)

            # decouple from parent environment
            os.chdir('/')
            os.setsid()
            os.umask(0)

            # do second fork
            try:
                pid = os.fork()
                if pid > 0:
                    sys.exit(0)
            except OSError, e:
                print >>sys.stderr, 'fork #2 failed: %d (%s)' % (
                    e.errno, e.strerror)
                sys.exit(1)

            # write pid file
            try:
                pidfile = open(build.pid_path, 'w')
                pidfile.write(str(os.getpid()) + '\n')
                pidfile.close()
            except IOError:
                print >>sys.stderr, 'could not write pid-file: ', build.pid_path
                sys.exit(1)

        # start the daemon main loop
        self.daemon_main()

    def daemon_main(self):
        """daemon entry point"""

        # register SIGTERM handler
        signal.signal(signal.SIGTERM, self.term_handler)

        # register d-bus service
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        system_bus = dbus.SystemBus()
        #name = dbus.service.BusName('org.thinkpad.fancontrol.tpfand', system_bus)

        # create and load configuration
        act_settings = settings.Settings(system_bus, '/Settings')

        # create controller
        controller = control.Control(
            system_bus, '/Control', act_settings, self.debug)

        # start glib main loop
        mainloop = gobject.MainLoop()
        mainloop.run()

    def term_handler(self, signum, frame):
        """handles SIGTERM"""
        controller.set_speed(255)
        try:
            os.remove(build.pid_path)
        except:
            pass
        mainloop.quit()


def main():

    app = Tpfand()

if __name__ == '__main__':
    main()
