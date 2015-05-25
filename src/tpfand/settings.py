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
import os.path
import sys

import dbus.service

class ProfileNotOverriddenException(dbus.DBusException):
    _dbus_error_name = 'org.thinkpad.fancontrol.ProfileNotOverriddenException'


class Settings(dbus.service.Object):

    """profile and config settings"""
    profile_as_string = ''
    # user options
    enabled = False
    override_profile = False

    # profile / user overrideable options
    sensor_names = {}
    trigger_points = {}
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

        self.profile_path = os.path.split(
            config_path)[0] + '/' + self.current_profile

        dbus.service.Object.__init__(self, bus, path)

        self.read_model_info()
        self.load()

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='', out_signature='a{ss}')
    def get_model_info(self):
        """returns hardware model info"""
        return {'vendor': self.product_pretty_vendor,
                'name': self.product_pretty_name,
                'id': self.product_pretty_id,
                'profile_name': self.product_name,
                'profile_id': self.product_id}

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='', out_signature='as')
    def get_loaded_profiles(self):
        """returns a list of the given profiles"""
        return self.loaded_profiles

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='', out_signature='s')
    def get_profile_comment(self):
        """returns the comment for the last loaded profile"""
        if self.override_profile:
            return ''
        else:
            return self.profile_comment

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='', out_signature='b')
    def is_profile_exactly_matched(self):
        """returns True if profile exactly matches hardware"""
        return self.id_match

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='', out_signature='')
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

        # load the profile
        if self.enabled:
            if self.override_profile:
                self.load_profile(self.read_profile(
                    self.get_profile_path(self.current_profile)))
            else:
                profile_from_db, _, id_match = self.get_profile_file_list()
                if id_match:
                    self.load_profile(self.read_profile(
                        profile_from_db))

        self.verify()

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='', out_signature='')
    def save(self):
        """saves config to disk"""
        self.write_profile(self.profile_path)

    # TODO: needs to be improved
    def get_profile_file_list(self):
        """returns a list of profile files to load for this system"""

        profile_file = ''
        profile = ''

        # match parts of product name
        #product_path = product_name_dir + self.product_name
        # for n in range(len(product_name_dir) + 1, len(product_path)):
        #    path = product_path[0:n]
        #    if os.path.isfile(path):
        #        files.append(path)
        #        profiles.append(path[len(model_dir):])

        # try matching model id
        id_match = False
        model_path = self.supplied_profile_dir + self.product_id
        if os.path.isfile(model_path):
            profile_file = model_path
            profile = model_path[len(model_dir):]
            id_match = True

        return profile_file, profile, id_match

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
            print 'Warning: unable to get information about your system!'
            self.product_id = ''
            self.product_name = ''
            self.product_pretty_vendor = ''
            self.product_pretty_name = ''
            self.product_pretty_id = ''

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='', out_signature='a{is}')
    def get_sensor_names(self):
        """returns the sensor names"""
        return self.sensor_names

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='a{is}', out_signature='')
    def set_sensor_names(self, tset):
        """sets the sensor names"""
        self.verify_profile_overridden()
        self.sensor_names = tset
        self.verify()
        self.save()

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='', out_signature='a{ia{ii}}')
    def get_trigger_points(self):
        """returns the temperature trigger points for the sensors"""
        return self.trigger_points

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='a{ia{ii}}', out_signature='')
    def set_trigger_points(self, tset):
        """sets the temperature trigger points for the sensors"""
        self.verify_profile_overridden()
        self.trigger_points = tset
        self.verify()
        self.save()

    def get_profile_path(self, profile):
        return os.path.split(
            self.config_path)[0] + '/' + profile

    # TODO: needs to be improved
    def verify(self):
        """Verifies that all settings are valid"""
        for n in range(0, self.get_sensor_count()):
            if n not in self.sensor_names or len(self.sensor_names[n].strip()) == 0:
                self.sensor_names[n] = 'Sensor ' + str(n)
            else:
                self.sensor_names[n] = self.sensor_names[
                    n].replace('=', '-').replace('\n', '')
            if n not in self.trigger_points:
                self.trigger_points[n] = {0: 255}
        for opt in ['hysteresis']:
            val = eval('self.' + opt)
            lmin, lmax = self.get_setting_limits(opt)
            if val < lmin or val > lmax:
                if val < lmin:
                    val = lmin
                if val > lmax:
                    val = lmax
                exec 'self.' + opt + ' = ' + str(val)

    def verify_profile_overridden(self):
        """verifies that override_profile is true, raises ProfileNotOverriddenException if it is not"""
        if not self.override_profile:
            raise ProfileNotOverriddenException()

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='', out_signature='i')
    def get_sensor_count(self):
        """returns the count of sensors"""
        return len(self.sensor_names)

    # TODO: needs to be improved
    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='s', out_signature='ad')
    def get_setting_limits(self, opt):
        """returns the limits (min, max) of the given option"""
        if opt == 'hysteresis':
            return [0, 10]
        else:
            return None

    # TODO: needs to be improved
    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='', out_signature='a{si}')
    def get_settings(self):
        """returns the settings"""
        ret = {'hysteresis': self.hysteresis,
               'enabled': int(self.enabled),
               'override_profile': int(self.override_profile)}
        return ret

    # TODO: needs to be improved
    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='a{si}', out_signature='')
    def set_settings(self, tset):
        """sets the settings"""
        try:
            if 'override_profile' in tset:
                self.override_profile = bool(tset['override_profile'])
            if 'enabled' in tset:
                self.enabled = bool(tset['enabled'])
            if 'hysteresis' in tset:
                self.verify_profile_overridden()
                self.hysteresis = tset['hysteresis']
        except ValueError, ex:
            print 'Error parsing parameters: ', ex
            pass
        finally:
            self.verify()
            self.save()
            if not self.override_profile:
                self.load_profile()
                self.verify()

    @dbus.service.method('org.thinkpad.fancontrol.Settings', in_signature='', out_signature='s')
    def get_profile_string(self):
        """returns the current profile as a string"""
        res = ''
        string_buffer = StringIO.StringIO(res)
        self.write_profile(string_buffer, is_a_string_buffer=True)
        print self.profile_as_string
        return self.profile_as_string

    def read_config(self, path):
        """Reads a configuration file"""

        settings_from_config = {}

        if self.debug:
            print "Parsing the configuration file located at " + path
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

        if self.debug:
            print "Parsing the profile file located at " + path

        try:
            settings_from_profile['file_path'] = path

            current_profile = ConfigParser.SafeConfigParser()
            current_profile.read(path)

            if current_profile.has_section('General'):
                if current_profile.has_option('General', 'comment'):
                    settings_from_profile['comment'] = current_profile.get(
                        'General', 'comment')
                    # verify that comment is valid unicode, otherwise
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

                for sensor in current_profile.options('Sensors'):

                    if 'ibm_thermal_sensor' in sensor:
                        tid = int(sensor.split('_')[3])
                        tid_conf = ast.literal_eval(
                            current_profile.get('Sensors', sensor))
                        trigger_dict = tid_conf['triggers']
                        if len(trigger_dict) > 0:
                            trigger_points[tid] = trigger_dict
                        sensor_names[tid] = tid_conf['name']
                    # TODO Parsing for hwmon sensors

                settings_from_profile['trigger_points'] = trigger_points
                settings_from_profile['sensor_names'] = sensor_names

        except Exception, e:
            print 'Error parsing profile file: %s' % path
            print e
            settings_from_profile['status'] = False
            return settings_from_profile
        settings_from_profile['status'] = True
        return settings_from_profile

    def write_config(self, path):
        """saves current configuration to the specified configuration file """

        if self.debug:
            print "Saving current configuration to " + path

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
            print 'Error reading curent configuration'
            print e
            return False

        try:
            config_file = open(path, 'w')
            config_file.write(
                '# This file provides the general configuration of tpfancod')
            config_file.write('\n\n\n')
            current_config.write(config_file)
            # config_file.close()

        except Exception, e:
            print 'Error writing config file: %s' % path
            print e
            return False
        return True

    def write_profile(self, path, is_a_string_buffer=False):
        """writes a fan profile file"""

        if self.debug:
            if is_a_string_buffer:
                print "Saving current profile to a string"
            else:
                print "Saving current profile to " + path

        try:
            current_profile = ConfigParser.SafeConfigParser(
                allow_no_value=True)

            current_profile.add_section('General')
            current_profile.set('General',
                                '# Short description of the purpose of this profile.')
            current_profile.set('General', 'comment', self.profile_comment)
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
            current_profile.set('Options', 'hysteresis', str(self.hysteresis))

            current_profile.add_section('Sensors')

            for sensor_id in set(self.sensor_names.keys()):
                current_profile.set('Sensors', 'ibm_thermal_sensor' + str(sensor_id), str(
                    {'name': self.sensor_names[sensor_id], 'triggers': self.trigger_points[sensor_id]}))

        except Exception, e:
            print 'Error reading curent profile'
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
        if settings_from_config['status'] and self.verify_config(settings_from_config):
            self.enabled = settings_from_config['enabled']
            self.override_profile = settings_from_config['override_profile']
            self.current_profile = settings_from_config['current_profile']
        else:
            print 'Error loading values from ' + settings_from_config['file_path']
            return False
        return True

    def load_profile(self, settings_from_profile):
        """apply settings from a profile"""
        if settings_from_profile['status'] and self.verify_profile(settings_from_profile):
            self.profile_comment = settings_from_profile['comment']
            self.hysteresis = settings_from_profile['hysteresis']
            self.trigger_points = settings_from_profile['trigger_points']
            self.sensor_names = settings_from_profile['sensor_names']
        else:
            print 'Error loading values from ' + settings_from_profile['file_path']
            return False
        return True

        profile_file_list, self.loaded_profiles, self.id_match = self.get_profile_file_list()
        if not self.override_profile:
            self.sensor_names = {}
            self.trigger_points = {}
            self.hysteresis = -1
            self.profile_comment = ''
            for path in profile_file_list:
                try:
                    # only show comment of profile that matches notebook model
                    # best
                    self.profile_comment = ''

                    self.read_profile(path)
                except Exception, ex:
                    print 'Error loading ', path, ': ', ex

    def verify_config(self, settings_from_config):
        """checks that settings form a configuration file are correct"""
        # Stub
        # TODO: proper checks
        return True

    def verify_profile(self, settings_from_config):
        """checks that settings form a profile file are correct"""
        # Stub
        # TODO: proper checks
        return True

    def verify_setting(self, setting_name, setting_value):
        """checks that a single setting is correct"""
        # Stub
        # TODO: proper checks
        return True
