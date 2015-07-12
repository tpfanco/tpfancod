#! /usr/bin/python2.7
# -*- coding: utf8 -*-
#
# tpfanco - controls the fan-speed of IBM/Lenovo ThinkPad Notebooks
# Copyright (C) 2011-2015 Vladyslav Shtabovenko
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
import ConfigParser
import StringIO
import ast
import logging
import os.path
import dbus.service


class ProfileNotOverriddenException(dbus.DBusException):
    _dbus_error_name = 'org.thinkpad.fancontrol.ProfileNotOverriddenException'


class Settings(dbus.service.Object):

    max_temp = 100
    option_limits = {'hysteresis': [0, 10]}
    profile_path = ''

    """profile and config settings"""
    profile_as_string = ''
    # user options
    enabled = False
    override_profile = False
    current_profile = ''

    # profile / user overrideable options
    sensor_names = {}
    trigger_points = {}
    sensor_scalings = {}
    hysteresis = 2

    # hardware product info
    product_name = None
    product_id = None
    product_pretty_vendor = None
    product_pretty_name = None
    product_pretty_id = None

    # profile info
    loaded_profiles = []

    # comments for the last loaded profile
    profile_comment = ''

    def __init__(self, bus, path, debug, quiet, no_ibm_thermal, version, config_path, current_profile, ibm_fan, ibm_thermal, supplied_profile_dir, poll_time, watchdog_time):
        self.logger = logging.getLogger(__name__)
        self.debug = debug
        self.quiet = quiet
        self.no_ibm_thermal = no_ibm_thermal
        self.version = version
        self.config_path = config_path
        self.current_profile = current_profile
        self.ibm_fan = ibm_fan
        self.ibm_thermal = ibm_thermal
        self.supplied_profile_dir = supplied_profile_dir
        self.poll_time = poll_time
        self.watchdog_time = watchdog_time
        self.id_match = False

        self.profile_path = os.path.split(
            config_path)[0] + '/' + self.current_profile

        dbus.service.Object.__init__(self, bus, path)

        if self.debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.ERROR)

        self.read_model_info()
        self.load()

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='a{ss}')
    def get_model_info(self):
        """returns hardware model info"""
        return {'vendor': self.product_pretty_vendor,
                'name': self.product_pretty_name,
                'id': self.product_pretty_id,
                'profile_name': self.product_name,
                'profile_id': self.product_id}

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='as')
    def get_loaded_profiles(self):
        """returns a list of the given profiles"""
        return self.loaded_profiles

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='s')
    def get_profile_comment(self):
        """returns the comment for the last loaded profile"""
        if self.override_profile:
            return ''
        else:
            return self.profile_comment

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='b')
    def is_profile_exactly_matched(self):
        """returns True if profile exactly matches hardware"""
        return self.id_match

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='')
    def load(self):
        """loads profile and config form disk"""

        self.enabled = False
        self.override_profile = False

        # if the configuration file is missing, create a new one
        if not os.path.isfile(self.config_path):
            self.write_config(self.config_path)

        # if the standard profile is missing, create a new one
        if not os.path.isfile(self.profile_path):
            self.write_profile(self.profile_path)

        # load the configuration

        self.load_config(self.read_config(self.config_path))
        self.auto_load_profile()
        self.verify_tpfancod_settings()

    def auto_load_profile(self):
        # load the profile
        if self.enabled:
            if self.override_profile:
                self.load_profile(self.read_profile(
                    self.get_profile_path(self.current_profile)))
            else:
                profile_from_db, id_match = self.get_profile_file_list()
                if id_match:
                    self.id_match = True
                    self.load_profile(self.read_profile(
                        profile_from_db))
                else:
                    self.id_match = False

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='')
    def save(self):
        """saves configuration and profile to disk"""
        self.write_config(self.config_path)
        self.write_profile(self.profile_path)

    def get_profile_file_list(self):
        """returns a list of profile files to load for this system"""
        profile_file = ''
        id_match = False
        model_path = self.supplied_profile_dir + self.product_id
        self.logger.debug('Looking for a profile in ' + model_path)
        if os.path.isfile(model_path):
            profile_file = model_path
            id_match = True
        return profile_file, id_match

    def read_model_info(self):
        """reads model info from /sys/class/dmi/id"""
        try:
            with open("/sys/class/dmi/id/product_name", 'r') as f:
                hw_product = f.read(256)
            with open("/sys/class/dmi/id/board_vendor", 'r') as f:
                hw_vendor = f.read(256)
            with open("/sys/class/dmi/id/product_version", 'r') as f:
                hw_version = f.read(256)
            product_id = hw_vendor + '_' + hw_product
            self.product_id = product_id.lower()
            product_name = hw_vendor.lower() + '_' + hw_version.lower()
            self.product_name = product_name.lower().replace(
                '/', '-').replace(' ', '_')

            self.product_pretty_vendor = hw_vendor
            self.product_pretty_name = hw_version
            self.product_pretty_id = hw_product
        except:
            self.logger.error(
                'Warning: unable to get information about your system!')
            self.product_id = ''
            self.product_name = ''
            self.product_pretty_vendor = ''
            self.product_pretty_name = ''
            self.product_pretty_id = ''

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='a{ss}')
    def get_sensor_names(self):
        """returns the sensor names"""
        return self.sensor_names

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='a{ss}', out_signature='')
    def set_sensor_names(self, tset):
        """sets the sensor names"""
        self.verify_profile_overridden()
        self.sensor_names = tset
        self.verify_tpfancod_settings()
        self.save()

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='a{sa{ss}}', out_signature='')
    def add_new_sensor(self, tset):
        """adds a new sensor"""
        sensor_id = tset['name'].iterkeys().next()
        new_trigger_points = {}

        self.sensor_names[sensor_id] = tset['name'][sensor_id]

        for n in tset[tset['name'].iterkeys().next()]:
            new_trigger_points[int(n)] = int(
                tset[tset['name'].iterkeys().next()][n])
        self.trigger_points[sensor_id] = new_trigger_points
        if tset['scaling'][sensor_id] != '':
            self.sensor_scaling[sensor_id] = float(tset['scaling'][sensor_id])
        self.save()
        # now load new custom profile into memory
        self.load()

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='a{sa{ii}}')
    def get_trigger_points(self):
        """returns the temperature trigger points for the sensors"""
        return self.trigger_points

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='a{sa{ii}}', out_signature='b')
    def set_trigger_points(self, tset):
        """sets the temperature trigger points for the sensors"""
        self.verify_profile_overridden()
        self.check_sensors_and_triggers(
            tset, self.sensor_names, self.sensor_scalings)
        self.trigger_points = tset
        self.verify_tpfancod_settings()
        self.save()
        # now load new custom profile into memory
        self.load()

    def get_profile_path(self, profile):
        return os.path.split(
            self.config_path)[0] + '/' + profile

    def check_sensors_and_triggers(self, trigger_points, sensor_names, sensor_scalings={}):
        '''Verifies that given sensors, triggers and sensor names are valid'''

        if sorted(trigger_points.keys()) != sorted(sensor_names.keys()):
            raise SyntaxError(
                'The number of sensors and sensor names do not match')
        for sensor in trigger_points:

            # some special checks for hwmon senesors
            if not sensor.isdigit():
                if not os.path.isfile(sensor):
                    raise SyntaxError(
                        'The sensor ' + sensor + 'doesn\'t exist')

                if sensor not in sensor_scalings:
                    raise SyntaxError(
                        'Missing the scaling factor for the sensor' + sensor)
                else:
                    if not isinstance(sensor_scalings[sensor], float):
                        raise SyntaxError(
                            'The scaling factor' + sensor_scalings[sensor] + ' for the sensor' + sensor + ' is not float')

            if len(sensor_names[sensor].strip()) == 0:
                raise SyntaxError(
                    'The sensor ' + sensor + 'doesn\'t have a name')
            if len(trigger_points[sensor]) == 0:
                raise SyntaxError(
                    'The sensor ' + sensor + 'doesn\'t triggers attached to it')
            for temp in trigger_points[sensor]:
                fan_level = trigger_points[sensor][temp]
                if not isinstance(temp, (int, long)):
                    raise SyntaxError(
                        'The temperature ' + str(temp) + 'is not an integer')
                if temp > self.max_temp or temp < 0:
                    raise SyntaxError(
                        'The temperature ' + str(temp) + 'is out of bounds')
                if not isinstance(fan_level, (int, long)):
                    raise SyntaxError(
                        'The fan level ' + str(fan_level) + 'is not an integer')
                if fan_level > 256 or fan_level < 0:
                    raise SyntaxError(
                        'The fan_level ' + str(fan_level) + 'is out of bounds')

    def check_setting(self, setting_name, setting_value):
        """Verifies that the value of the given setting is allowed"""
        # some settings are boolean, so we just need to check their type
        if setting_name in ['enabled', 'override_profile']:
            if not isinstance(setting_value, bool):
                raise SyntaxError(
                    'The value of ' + str(setting_name) + ' is out of bounds')
            else:
                return
        # other settings point to files, so we need to check if they exist
        if setting_name in ['current_profile']:
            if not os.path.isfile(os.path.split(self.config_path)[0] + '/' + setting_value):
                raise SyntaxError(
                    'The profile ' + str(setting_value) + ' doesn\'t exist')
            else:
                return

        lmin, lmax = self.get_setting_limits(setting_name)
        if setting_value < lmin or setting_value > lmax:
            raise SyntaxError(
                'The value of ' + str(setting_name) + 'is out of bounds')

    def verify_tpfancod_settings(self):
        """Verifies that all settings of tpfancod are valid"""

        # check sensors, triggers and sensor names
        self.check_sensors_and_triggers(
            self.trigger_points, self.sensor_names, self.sensor_scalings)

        # check single settings
        for opt in ['hysteresis', 'enabled', 'override_profile', 'current_profile']:
            val = eval('self.' + opt)
            self.check_setting(opt, val)

    def verify_profile_overridden(self):
        """verifies that override_profile is true, raises ProfileNotOverriddenException if it is not"""
        if not self.override_profile:
            raise ProfileNotOverriddenException()

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='i')
    def get_sensor_count(self):
        """returns the count of sensors"""
        return len(self.sensor_names)

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='s', out_signature='ad')
    def get_setting_limits(self, opt):
        """returns the limits (min, max) of the given option"""
        if opt in self.option_limits:
            return self.option_limits[opt]
        else:
            raise SyntaxError(
                'The settings ' + str(opt) + ' does not exist')

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='a{si}')
    def get_settings(self):
        """returns the settings"""
        ret = {'hysteresis': self.hysteresis,
               'enabled': int(self.enabled),
               'override_profile': int(self.override_profile),
               'poll_time': int(self.poll_time)}
        return ret

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='a{ss}', out_signature='')
    def set_settings(self, tset):
        """sets the settings"""
        # check that all the settings are OK
        for setting in tset:
            val = tset[setting]
            if setting in ['enabled', 'override_profile', 'hysteresis']:
                val = ast.literal_eval(val)
            self.check_setting(setting, val)
        # now let us set the values
        self.logger.debug(
            'Updating settings to ' + str(tset))
        if 'enabled' in tset:
            self.logger.debug(
                'Changing enabled to ' + str(ast.literal_eval(tset['enabled'])))
            self.enabled = ast.literal_eval(tset['enabled'])
        if 'override_profile' in tset:
            self.logger.debug(
                'Changing override_profile to ' + str(ast.literal_eval(tset['override_profile'])))
            self.override_profile = ast.literal_eval(tset['override_profile'])
        if 'hysteresis' in tset:
            self.verify_profile_overridden()
            self.logger.debug(
                'Changing hysteresis to ' + str(ast.literal_eval(tset['hysteresis'])))
            self.hysteresis = ast.literal_eval(tset['hysteresis'])
        if 'current_profile' in tset:
            self.verify_profile_overridden()
            self.logger.debug(
                'Changing current_profile to ' + str(ast.literal_eval(tset['current_profile'])))
            self.current_profile = tset['current_profile']
        self.verify_tpfancod_settings()
        self.save()
        # now load new custom profile into memory
        self.load()

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='s')
    def get_profile_string(self):
        """returns the current profile as a string"""
        res = ''
        string_buffer = StringIO.StringIO(res)
        self.write_profile(string_buffer, is_a_string_buffer=True)
        return self.profile_as_string

    def read_config(self, path):
        """Reads a configuration file"""

        settings_from_config = {}
        self.logger.debug('Parsing the configuration file located at ' + path)

        try:
            settings_from_config['file_path'] = path
            current_config = ConfigParser.SafeConfigParser()
            current_config.read(path)

            if current_config.has_section('General'):
                if current_config.has_option('General', 'enabled'):
                    settings_from_config['enabled'] = current_config.getboolean(
                        'General', 'enabled')

                if current_config.has_option('General', 'override_profile'):
                    settings_from_config['override_profile'] = current_config.getboolean(
                        'General', 'override_profile')

                if current_config.has_option('General', 'current_profile'):
                    settings_from_config['current_profile'] = current_config.get(
                        'General', 'current_profile')

        except Exception, e:
            print 'Error parsing config file: %s' % path
            print e
            settings_from_config['status'] = False
            return settings_from_config

        settings_from_config['status'] = True
        return settings_from_config

    def read_profile(self, path):
        """Reads a fan profile file"""

        settings_from_profile = {}
        self.logger.debug('Parsing the profile file located at ' + path)

        try:
            settings_from_profile['file_path'] = path

            current_profile = ConfigParser.SafeConfigParser()
            current_profile.read(path)

            if current_profile.has_section('General'):
                if current_profile.has_option('General', 'comment'):
                    settings_from_profile['comment'] = current_profile.get(
                        'General', 'comment')
                    # verify_tpfancod_settings that comment is valid unicode, otherwise
                    # use Latin1 coding
                    try:
                        unicode(settings_from_profile['comment'])
                    except UnicodeDecodeError:
                        settings_from_profile['comment'] = settings_from_profile[
                            'comment'].decode("latin1")

                if current_profile.has_option('General', 'product_vendor'):
                    settings_from_profile['product_pretty_vendor'] = current_profile.get(
                        'General', 'product_vendor')
                if current_profile.has_option('General', 'product_name'):
                    settings_from_profile['product_pretty_name'] = current_profile.get(
                        'General', 'product_name')
                if current_profile.has_option('General', 'product_id'):
                    settings_from_profile['product_pretty_id'] = current_profile.get(
                        'General', 'product_id')

            if current_profile.has_section('Options'):
                if current_profile.has_option('Options', 'hysteresis'):
                    settings_from_profile['hysteresis'] = current_profile.getint(
                        'Options', 'hysteresis')

            if current_profile.has_section('Sensors'):
                trigger_points = {}
                sensor_names = {}
                sensor_scalings = {}

                for sensor in current_profile.options('Sensors'):

                    self.logger.debug('Parsing sensor ' + sensor)
                    if not sensor.startswith('ibm_thermal_sensor') and not sensor.startswith('/'):
                        continue
                    tid_conf = ast.literal_eval(
                        current_profile.get('Sensors', sensor))
                    trigger_dict = tid_conf['triggers']

                    if sensor.startswith('ibm_thermal_sensor'):
                        tid = sensor.split('_')[3]
                        sensor_names[tid] = tid_conf['name']
                        trigger_points[tid] = trigger_dict

                    if sensor.startswith('/'):
                        sensor_names[sensor] = tid_conf['name']
                        sensor_scalings[sensor] = tid_conf['scaling']
                        trigger_points[sensor] = trigger_dict

                settings_from_profile['trigger_points'] = trigger_points
                settings_from_profile['sensor_names'] = sensor_names
                settings_from_profile['sensor_scalings'] = sensor_scalings

        except Exception, e:
            print 'Error parsing profile file: %s' % path
            print e
            settings_from_profile['status'] = False
            return settings_from_profile
        settings_from_profile['status'] = True
        return settings_from_profile

    def write_config(self, path):
        """saves current configuration to the specified configuration file """

        self.logger.debug('Saving current configuration to ' + path)

        try:
            current_config = ConfigParser.SafeConfigParser(allow_no_value=True)

            current_config.add_section('General')
            current_config.set('General',
                               '# Set this to True to allow tpfancod control the fan of your machine.')
            current_config.set('General', 'enabled', str(self.enabled))
            current_config.set('General',
                               '# If a profile for your ThinkPad model is available in the database,')
            current_config.set('General',
                               '# tpfancod will use it by default and ignore any profiles you have')
            current_config.set('General',
                               '# in /etc/tpfancod. Set this to True to use custom profiles.')
            current_config.set(
                'General', 'override_profile', str(self.override_profile))
            current_config.set('General',
                               '# This determines the current custom profile used by tpfancod. The profile')
            current_config.set('General',
                               '# must be placed in /etc/tpfancod and begin with profile_, e.g.')
            current_config.set('General',
                               '# profile_library  or profile_gaming. This option works only if')
            current_config.set('General',
                               '# override_profile is set to True.')
            current_config.set(
                'General', 'current_profile', self.current_profile)

        except Exception, e:
            print 'Error reading current configuration'
            print e
            return False

        try:
            config_file = open(path, 'w')
            config_file.write(
                '# This file provides the general configuration of tpfancod')
            config_file.write('\n\n\n')
            current_config.write(config_file)
            config_file.close()

        except Exception, e:
            print 'Error writing config file: %s' % path
            print e
            return False
        return True

    def write_profile(self, path, is_a_string_buffer=False):
        """writes a fan profile file"""

        if is_a_string_buffer:
            self.logger.debug('Saving current profile to a string')
        else:
            self.logger.debug('Saving current profile to ' + path)

        try:
            current_profile = ConfigParser.SafeConfigParser(
                allow_no_value=True)

            current_profile.add_section('General')
            current_profile.set('General',
                                '# Short description of the purpose of this profile.')
            current_profile.set(
                'General', 'comment', self.profile_comment)
            current_profile.set('General', '# System manufacturer')
            current_profile.set(
                'General', 'product_vendor', self.product_pretty_vendor)
            current_profile.set('General', '# ThinkPad Model')
            current_profile.set(
                'General', 'product_name', self.product_pretty_name)
            current_profile.set('General', '# Machine type')
            current_profile.set(
                'General', 'product_id', self.product_pretty_id)
            current_profile.add_section('Options')
            current_profile.set('Options',
                                '# Set the hysteresis temperature difference.')
            current_profile.set(
                'Options', 'hysteresis', str(self.hysteresis))
            current_profile.add_section('Sensors')

            for sensor_id in set(self.sensor_names.keys()):
                ntp = {}
                for tp in self.trigger_points[sensor_id]:
                    ntp[int(tp)] = int(self.trigger_points[sensor_id][tp])
                nname = str(self.sensor_names[sensor_id])

                if sensor_id.isdigit():
                    current_profile.set('Sensors', 'ibm_thermal_sensor_' + str(sensor_id), str(
                        {'name': nname, 'triggers': ntp}))
                else:
                    current_profile.set('Sensors', str(sensor_id), str(
                        {'name': nname, 'scaling': self.sensor_scalings[sensor_id], 'triggers': ntp}))

        except Exception, e:
            print 'Error writing curent profile'
            print e
            return False

        try:
            if not is_a_string_buffer:
                path = open(path, 'w')
            path.write(
                '# This file contains a fan profile for tpfancod')
            path.write('\n\n\n')
            current_profile.write(path)
            if is_a_string_buffer:
                self.profile_as_string = path.getvalue()

        except Exception, e:
            print 'Error writing profile file: %s' % path
            print e
            return False
        return True

    def load_config(self, settings_from_config):
        """apply settings from a config"""
        self.verify_config(settings_from_config)
        if settings_from_config['status']:
            self.enabled = settings_from_config['enabled']
            self.override_profile = settings_from_config['override_profile']
            self.current_profile = settings_from_config['current_profile']

        else:
            raise SyntaxError(
                'Error loading values from ' + settings_from_config['file_path'])

    def load_profile(self, settings_from_profile):
        """apply settings from a profile"""
        self.verify_profile(settings_from_profile)
        if settings_from_profile['status']:
            self.profile_comment = settings_from_profile['comment']
            self.hysteresis = settings_from_profile['hysteresis']
            self.trigger_points = settings_from_profile['trigger_points']
            self.sensor_names = settings_from_profile['sensor_names']
            self.sensor_scalings = settings_from_profile['sensor_scalings']
        else:
            raise SyntaxError(
                'Error loading values from ' + settings_from_profile['file_path'])

    def verify_config(self, settings_from_config):
        """checks that settings form a configuration file are correct"""
        for opt in ['enabled', 'override_profile', 'current_profile']:
            self.check_setting(opt, settings_from_config[opt])

    def verify_profile(self, settings_from_profile):
        """checks that settings form a profile file are correct"""
        self.check_sensors_and_triggers(settings_from_profile['trigger_points'],
                                        settings_from_profile['sensor_names'],
                                        settings_from_profile['sensor_scalings'])
        for opt in ['hysteresis']:
            self.check_setting(opt, settings_from_profile[opt])

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='as')
    def get_available_ibm_thermal_sensors(self):
        res = []
        try:
            tempfile = open(self.ibm_thermal, 'r')
            elements = tempfile.readline().split()[1:]
            tempfile.close()
            for idx, val in enumerate(elements):
                # value is +/-128 or 0, if sensor is disconnected
                if abs(int(val)) != 128 and abs(int(val)) != 0:
                    res.append(str(idx))
        except IOError:
            # sometimes read fails during suspend/resume
            pass
        finally:
            try:
                tempfile.close()
            except:
                pass
        return res

    @dbus.service.method('org.tpfanco.tpfancod.Settings', in_signature='', out_signature='b')
    def check_if_hwmon_sensor_exists(self, sensor):
        return os.path.isfile(sensor)
