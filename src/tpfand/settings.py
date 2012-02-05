#! /usr/bin/python
# -*- coding: utf8 -*-
#
# tpfanco - controls the fan-speed of IBM/Lenovo ThinkPad Notebooks
# Copyright (C) 2011-2012 Vladyslav Shtabovenko
# Copyright (C) 2007-2008 Sebastian Urban
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

import sys
if not ('/usr/share/pyshared' in sys.path):
    sys.path.append('/usr/share/pyshared')


import sys, os, os.path
import dbus, dbus.service, dbus.mainloop.glib, dbus.glib
import gobject
import dmidecode

from tpfand import build

class ProfileNotOverriddenException(dbus.DBusException):
    _dbus_error_name = "org.thinkpad.fancontrol.ProfileNotOverriddenException"

class Settings(dbus.service.Object):
    """profile and config settings"""
    
    # user options
    enabled = False    
    override_profile = False
    
    # profile / user overrideable options
    sensor_names = { }
    trigger_points = { }
    hysteresis = -1
    
    # hardware product info    
    product_name = None
    product_id = None
    product_pretty_vendor = None
    product_pretty_name = None
    product_pretty_id = None
    
    # profile info
    loaded_profiles = [ ]
    
    # comments for the last loaded profile
    profile_comment = ""

    def __init__(self, bus, path):
        dbus.service.Object.__init__(self, bus, path)
        self.read_model_info()
        self.load()
        
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='', out_signature='a{ss}') 
    def get_model_info(self):
        """returns hardware model info"""
        return {'vendor': self.product_pretty_vendor,
                'name': self.product_pretty_name,
                'id': self.product_pretty_id,
                'profile_name': self.product_name,
                'profile_id': self.product_id }
        
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='', out_signature='as') 
    def get_loaded_profiles(self):
        """returns a list of the given profiles"""
        return self.loaded_profiles  
    
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='', out_signature='s')
    def get_profile_comment(self):
        """returns the comment for the last loaded profile"""
        if self.override_profile:
            return ""
        else:
            return self.profile_comment
    
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='', out_signature='b') 
    def is_profile_exactly_matched(self):
        """returns True if profile exactly matches hardware"""     
        return self.id_match
    
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='', out_signature='')
    def load(self):
        """loads profile and config form disk"""
        self.enabled = False    
        self.override_profile = False
        if os.path.isfile(build.config_path):
            self.read_config(build.config_path, True)
        self.load_profile()
        self.verify()
                
    def load_profile(self):
        """loads profile from disk"""
        profile_file_list, self.loaded_profiles, self.id_match = self.get_profile_file_list()
        if not self.override_profile:  
            self.sensor_names = { }
            self.trigger_points = { }
            self.hysteresis = -1
            self.profile_comment = ""
            for path in profile_file_list:
                try:
                    # only show comment of profile that matches notebook model best
                    self.profile_comment = ""
                    
                    self.read_config(path, False)
                except Exception, ex:
                    print "Error loading ", path, ": ", ex        
            
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='', out_signature='') 
    def save(self):
        """saves config to disk"""
        self.write_config(build.config_path)
        
    def get_profile_file_list(self):
        """returns a list of profile files to load for this system"""
        model_dir = build.data_dir + 'models/'
        product_id_dir = model_dir + 'by-id/'
        product_name_dir = model_dir + 'by-name/'
                
        # generic profile
        files = [model_dir + "generic"]
        profiles = [ "generic" ]
        
        # match parts of product name
        product_path = product_name_dir + self.product_name
        for n in range(len(product_name_dir)+1, len(product_path)):
            path = product_path[0:n]
            if os.path.isfile(path):
                files.append(path)
                profiles.append(path[len(model_dir):])
                
        # try matching model id
        id_match = False
        model_path = product_id_dir + self.product_id
        if os.path.isfile(model_path):
            files.append(model_path)
            profiles.append(model_path[len(model_dir):])
            id_match = True
                        
        return files, profiles, id_match
        
    def read_model_info(self):
        """reads model info using dmidecode module"""
        try:
            current_system = dmidecode.system()                   
            hw_product = current_system['0x0001']['data']['Product Name']
            hw_vendor = current_system['0x0001']['data']['Manufacturer']
            hw_version = current_system['0x0001']['data']['Version']
            product_id = hw_vendor + "_" + hw_product
            self.product_id = product_id.lower()
            product_name = hw_vendor.lower() + "_" + hw_version.lower()
            self.product_name = product_name.lower().replace('/', '-').replace(' ', '_')
            
            self.product_pretty_vendor = hw_vendor
            self.product_pretty_name = hw_version
            self.product_pretty_id = hw_product
        except:
            print "Warning: unable to get your system model from dmidecode"
            self.product_id = ''
            self.product_name = ''
            self.product_pretty_vendor = ''
            self.product_pretty_name = ''
            self.product_pretty_id = ''   
                
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='', out_signature='a{is}')
    def get_sensor_names(self):
        """returns the sensor names"""
        return self.sensor_names
    
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='a{is}', out_signature='')
    def set_sensor_names(self, set):
        """sets the sensor names"""
        self.verify_profile_overridden()
        self.sensor_names = set
        self.verify()
        self.save()
        
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='', out_signature='a{ia{ii}}')    
    def get_trigger_points(self):
        """returns the temperature trigger points for the sensors"""
        return self.trigger_points
    
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='a{ia{ii}}', out_signature='')
    def set_trigger_points(self, set):
        """sets the temperature trigger points for the sensors"""
        self.verify_profile_overridden()
        self.trigger_points = set
        self.verify()
        self.save()
        
    def verify(self):
        """Verifies that all settings a valid"""
        for n in range(0, self.get_sensor_count()):
            if n not in self.sensor_names or len(self.sensor_names[n].strip()) == 0:
                self.sensor_names[n] = "Sensor " + str(n)
            else:
                self.sensor_names[n] = self.sensor_names[n].replace("=", "-").replace("\n", "")
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
                    
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='', out_signature='i')        
    def get_sensor_count(self):
        """returns the count of sensors"""
        return 16
    
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='s', out_signature='ad')
    def get_setting_limits(self, opt):
        """returns the limits (min, max) of the given option"""
        if opt == 'hysteresis':
            return [0, 10]
        else:
            return None
    
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='', out_signature='a{si}')
    def get_settings(self):
        """returns the settings"""
        ret = {'hysteresis': self.hysteresis,
               'enabled': int(self.enabled),
               'override_profile': int(self.override_profile)}       
        return ret
    
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='a{si}', out_signature='')        
    def set_settings(self, set):
        """sets the settings"""
        try:
            if 'override_profile' in set:
                self.override_profile = bool(set['override_profile'])   
            if 'enabled' in set:
                self.enabled = bool(set['enabled'])                        
            if 'hysteresis' in set:
                self.verify_profile_overridden()
                self.hysteresis = set['hysteresis']           
        except ValueError, ex:
            print "Error parsing parameters: ", ex
            pass
        finally:
            self.verify()
            self.save()
            if not self.override_profile:
                self.load_profile()
                self.verify()
    
    def write_config(self, path):
        """Writes a fan profile file"""
        file = open(path, 'w')
        file.write("""#
# tp-fancontrol configuration file
#
# Options:
# enabled = [True / False]
# override_profile = [True / False]
# hysteresis = [hysteresis temperature difference]
#
# Trigger point syntax:
# [sensor-id]. [human readable sensor name] = [temperature]:[fan level] ...
# [fan level] = 0: fan off
# [fan level] = 1: interval cooling mode
# [fan level] = 255: hardware controlled cooling mode
# default rule is used for all unspecified sensors
#
# override_profile = True has to be specified before profile parameters
# or trigger points are changed in the configuration file.
# tpfand may regenerate this file at any time. Custom comments will be lost.
#

""")
        file.write("enabled = %s\n" % str(self.enabled))
        file.write("override_profile = %s\n" % str(self.override_profile))
        file.write("\n")
                    
        if self.override_profile:
            file.write(self.get_profile_string())
            
        file.close()
    
    @dbus.service.method("org.thinkpad.fancontrol.Settings", in_signature='', out_signature='s')  
    def get_profile_string(self):
        """returns the current profile as a string"""
        res = ""
        ids = set(self.sensor_names.keys())
        ids.union(set(self.trigger_points.keys()))
        for id in ids:
            if id in self.sensor_names:
                name = self.sensor_names[id]
            else:
                name = ""
            line = str(id) + ". " + name
            if id in self.trigger_points:
                line += " = "
                points = self.trigger_points[id]
                temps = points.keys()
                temps.sort()
                for temp in temps:
                    level = points[temp]
                    line += "%d:%d " % (temp, level)
            res += line + '\n'
        
        res += '\n'
        res += "hysteresis = %d\n" % self.hysteresis
        return res
    
    def read_config(self, path, is_config):
        """Reads a fan profile file"""
        file = open(path, 'r')
        for line in file.readlines():
            line = line.split('#')[0].strip()
            if len(line) > 0:
                try:
                    if (line.count('.') and line.count('=') and line.find('.') < line.find('=')) or (line.count('.') and not line.count('=')):
                        if (is_config and self.override_profile) or (not is_config and not self.override_profile): 
                            id, rest = line.split('.', 1)
                            id = id.strip()
                            id = int(id)
                                
                            if rest.count('='):
                                name, triggers = rest.split('=', 1)
                                name = name.strip()
                                points = { }
                                for trigger in triggers.strip().split(' '):
                                    trigger = trigger.strip()
                                    if len(trigger) > 0:
                                        temp, level = trigger.split(':')
                                        temp = int(temp)
                                        points[temp] = int(level)
                                if len(points) > 0:
                                    self.trigger_points[id] = points                                                                                                                     
                            else:
                                name = rest.strip()
                                triggers = None
                            if len(name) > 0:
                                self.sensor_names[id] = name
                            
                    elif line.count('='):
                        option, value = line.split('=', 1)
                        option = option.strip()
                        value = value.strip()
                        if option == 'hysteresis' and ((is_config and self.override_profile) or not is_config):
                            self.hysteresis = int(value)
                        elif option == 'enabled' and is_config:
                            self.enabled = (value == 'True')
                        elif option == 'override_profile' and is_config:
                            self.override_profile = (value == 'True')
                        elif option == 'comment' and not is_config:
                            self.profile_comment = value.replace("\\n", "\n")
                            # verify that comment is valid unicode, otherwise use Latin1 coding
                            try:
                                unicode(self.profile_comment)
                            except UnicodeDecodeError:
                                self.profile_comment = self.profile_comment.decode("latin1")
                except Exception, e:
                    print "Error parsing line: %s" % line
                    print e
        file.close()        
