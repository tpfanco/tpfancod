import unittest
import dbus.mainloop.glib
from tpfand import settings as tpfand_settings


class SettingsTestCase(unittest.TestCase):

    def setUp(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.system_bus = dbus.SystemBus()
        self.settings = tpfand_settings.Settings(self.system_bus, '/Settings',
                                                 # debug
                                                 False,
                                                 # quiet
                                                 False,
                                                 # no_ibm_thermal
                                                 False,
                                                 '1.0.0',  # version
                                                 # config_path
                                                 '/etc/tpfancod/settings.conf',
                                                 # current_profile
                                                 'profile_standard',
                                                 # ibm_fan
                                                 '/proc/acpi/ibm/fan',
                                                 # ibm_thermal
                                                 '/proc/acpi/ibm/thermal',
                                                 # supplied_profile_dir
                                                 '/usr/share/tpfacod-profiles/',
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
            self.settings.config_path, '/etc/tpfancod/settings.conf')
        self.assertEqual(self.settings.current_profile, 'profile_standard')
        self.assertEqual(self.settings.ibm_fan, '/proc/acpi/ibm/fan')
        self.assertEqual(self.settings.ibm_thermal, '/proc/acpi/ibm/thermal')
        self.assertEqual(
            self.settings.supplied_profile_dir, '/usr/share/tpfacod-profiles/')
        self.assertEqual(self.settings.poll_time, 3500)
        self.assertEqual(self.settings.watchdog_time, 5)

    def test_get_model_info(self):
        model_info = self.settings.get_model_info()
        self.assertEqual(model_info['vendor'], 'LENOVO\n')

    if __name__ == '__main__':
        unittest.main()
