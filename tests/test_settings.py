import errno
import os
import unittest

import dbus.mainloop.glib

from tpfancod import settings as tpfancodSettings


class SettingsTestCase(unittest.TestCase):

    def setUp(self):

        tpfancodSettingsSettings = tpfancodSettings.Settings
        try:
            os.makedirs('/tmp/etc/tpfancod/')
            os.makedirs('/tmp/usr/share/tpfancod-profiles/')
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.system_bus = dbus.SystemBus()
        self.settings = tpfancodSettingsSettings(self.system_bus, '/Settings',
                                                 # debug
                                                 False,
                                                 # quiet
                                                 False,
                                                 # no_ibm_thermal
                                                 False,
                                                 '1.0.0',  # version
                                                 # config_path
                                                 '/tmp/etc/tpfancod/settings.conf',
                                                 # current_profile
                                                 'profile_standard',
                                                 # ibm_fan
                                                 '/proc/acpi/ibm/fan',
                                                 # ibm_thermal
                                                 '/proc/acpi/ibm/thermal',
                                                 # supplied_profile_dir
                                                 '/tmp/usr/share/tpfancod-profiles/',
                                                 # poll_time
                                                 3500,
                                                 # watchdog_time
                                                 5)

    def tearDown(self):
        # It's important that we call remove_from_connection() here,
        # otherwise second test will try to add '/Settings' again which
        # would lead to
        # KeyError: "Can't register the object-path handler for '/Settings':
        # there is already a handler"
        self.settings.remove_from_connection()
        self.settings = None

    def test_input(self):
        self.assertEqual(self.settings.debug, False)
        self.assertEqual(self.settings.quiet, False)
        self.assertEqual(self.settings.no_ibm_thermal, False)
        self.assertEqual(self.settings.version, '1.0.0')
        self.assertEqual(
            self.settings.config_path, '/tmp/etc/tpfancod/settings.conf')
        self.assertEqual(self.settings.current_profile, 'profile_standard')
        self.assertEqual(self.settings.ibm_fan, '/proc/acpi/ibm/fan')
        self.assertEqual(self.settings.ibm_thermal, '/proc/acpi/ibm/thermal')
        self.assertEqual(
            self.settings.supplied_profile_dir, '/tmp/usr/share/tpfancod-profiles/')
        self.assertEqual(self.settings.poll_time, 3500)
        self.assertEqual(self.settings.watchdog_time, 5)

    def test_get_model_info(self):
        model_info = self.settings.get_model_info()
        self.assertEqual(model_info['vendor'], 'LENOVO\n')

    if __name__ == '__main__':
        unittest.main()
