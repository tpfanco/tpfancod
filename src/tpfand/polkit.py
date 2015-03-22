#!/usr/bin/python2.7
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

import os
import sys

import dbus
from dbus.mainloop.glib import DBusGMainLoop
import dbus.service
import gobject


class Polkit(object):

    """Class that allows interaction with PolicyKit via D-Bus"""

    policy_kit = None
    pk_authority = None
    change_settings_allowed = False

    def check_status(self, action_id, sender, link):
        pk_allowed = None
        pk_extra = None
        pk_info = None

        try:
            dbus_link = link.get_object(
                'org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False)
            dbus_info = dbus.Interface(dbus_link, 'org.freedesktop.DBus')
            pid = dbus_info.GetConnectionUnixProcessID(sender)
            print 'Checking now'
            (pk_allowed, pk_extra, pk_info) = self.pk_authority.CheckAuthorization(('unix-process', {'pid': dbus.UInt32(
                pid, variant_level=1), 'start-time': dbus.UInt64(0, variant_level=1)}), action_id, {'': ''}, dbus.UInt32(0), '', timeout=600)
        except Exception, ex:
            print 'Errors checking the authorization status via PolicyKit: ', ex
            return False

        if pk_allowed:
            return True
        else:
            return False

    def authorize(self, action_id, sender, link):
        pk_allowed = None
        pk_extra = None
        pk_info = None

        try:
            dbus_link = link.get_object(
                'org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False)
            dbus_info = dbus.Interface(dbus_link, 'org.freedesktop.DBus')
            pid = dbus_info.GetConnectionUnixProcessID(sender)
            (pk_allowed, pk_extra, pk_info) = self.pk_authority.CheckAuthorization(('unix-process', {'pid': dbus.UInt32(
                pid, variant_level=1), 'start-time': dbus.UInt64(0, variant_level=1)}), action_id, {'': ''}, dbus.UInt32(1), '', timeout=600)
        except Exception, ex:
            print 'Error obtaining authorization via PolicyKit: ', ex
            return False

        if pk_allowed:
            return True
        else:
            return False

    def authorize(self, action_id, pid):
        pk_allowed = None
        pk_extra = None
        pk_info = None

        try:
            (pk_allowed, pk_extra, pk_info) = self.pk_authority.CheckAuthorization(('unix-process', {'pid': dbus.UInt32(
                pid, variant_level=1), 'start-time': dbus.UInt64(0, variant_level=1)}), action_id, {'': ''}, dbus.UInt32(1), '', timeout=600)
        except Exception, ex:
            print 'Error obtaining authorization via PolicyKit: ', ex
            return False

        if pk_allowed:
            return True
        else:
            return False

    def __init__(self, service_dbus, policy_kit, pk_authority):
        gobject.threads_init()
        self.system_bus = service_dbus
        self.policy_kit = policy_kit
        self.pk_authority = pk_authority


def main():
    if os.geteuid() != 0:
        print 'Only root can run this script!'
        sys.exit(1)
    if len(sys.argv) != 3:
        print 'Too little or too much arguments'
        sys.exit(1)
    name = sys.argv[1]
    pid = sys.argv[2]
    try:
        system_bus = dbus.SystemBus()
        policy_kit = system_bus.get_object(
            'org.freedesktop.PolicyKit1', '/org/freedesktop/PolicyKit1/Authority')
        pk_authority = dbus.Interface(
            policy_kit, 'org.freedesktop.PolicyKit1.Authority')
        tp_polkit = Polkit(system_bus, policy_kit, pk_authority)
        tp_polkit.authorize(name, pid)
    except Exception, ex:
        print 'Error connecting to PolicyKit. Do you have PolicyKit installed?', ex
        exit(1)
    return 0

if __name__ == '__main__':
    main()
