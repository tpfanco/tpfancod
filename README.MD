# Warning

__This repository contains experimental code that is not ready for 
productive use. It is really not meant to be used on the daily basis and should be considered unstable. Use it on your own risk and only if you absolutely understand what you are doing!__

If you are looking for a stable branch, use the one from

https://github.com/tpfanco/tpfanco-legacy

The code in this repository is not yet ready for productive use!
Use it on your own risk!

# Disclaimer 

By enabling software control of the system fan, you can void you warranty and damage or shorten the lifespan of your notebook. If you decide to use Tpfanco, you agree to hold us blameless for any damages or data loss that arise from the use of this software.

This project does not have any affiliation with Lenovo or IBM! 

# Tpfanco 

## Description

Tpfanco is a free and open source fan control software for IBM/Lenovo ThinkPads running GNU/Linux. It consists of a fan control daemon and a GUI to monitor temperature sensor values and set thresholds. For selected ThinkPad models user-generated fan profiles are available. 

## Legacy 

Tpfanco is a fork of ThinkPad Fan Control ([tp-fan](https://launchpad.net/tp-fan)) by Sebastian Urban.

## Tpfanco daemon (tpfancod)

tpfancod is the main part of tpfanco. It is a daemon that runs in the background and controls the system fan of ThinkPad notebooks based on specified temperature profiles

## Requirements

* Python 2.7
* DBus with bindings for Python
* thinkpad_acpi kernel module loaded with fan_control=1 to enable fan control.

## Installation

Packages for the development version are currently not available. The following sections describe manual installation via `make`

### systemd based distributions

* Run
    ```
    sudo make install-systemd
    sudo systemctl enable tpfancod
    ```

* Reboot your system to reload `thinkpad_acpi` module with the
  `fan_control=1`option.

* Check that tpfanco is running properly via
    ```
    systemctl status tpfancod
    ```
### sysvinit based distributions

* Run
    ```
    sudo make install-sysvinit
    ```

* Reboot your system to reload `thinkpad_acpi` module with the
  `fan_control=1`option.

## Uninstall

* You can uninstall tpfancod by running

    ```
    sudo make uninstall
    ```

## Configuration

* The configuration file is `/etc/tpfancod/settings.conf`.
  After manual changes to this configuration file tpfancod must
  be restarted (e.g. via ` sudo systemctl restart tpfancod`)

* To allow tpfancod control your fan, you must change both `enabled` and
  `override_profile` to `True`

* Then, in `/etc/tpfancod/profile_standard` you can specify the triggers
  for the fan control.

* Here is an example `profile_standard` (some setting names might change in future)
  for a Lenovo Thinkpad X200. Note that this configuration uses both sensors from
  `/proc/acpi/ibm/thermal` and `/sys/devices/virtual/hwmon` which was not possible with
  the old versions. Of course, if `/proc/acpi/ibm/thermal` is not available (which is the case
  on some Thinkpads), tpfancod can use only hwmon sensors.
  
  			
        # This file contains a fan profile for tpfancod
        [General]
        # short description of the purpose of this profile.
        comment =
        # system manufacturer
        product_vendor = LENOVO
        # thinkpad model
        product_name = ThinkPad X200
        # machine type
        product_id = 7459GH6

        [Options]
        # set the hysteresis temperature difference.
        hysteresis = 2

        [Sensors]
        /sys/devices/virtual/hwmon/hwmon0/temp1_input = {'name':'Sensor 15','scaling':0.001,'triggers':{0:255}}
        /sys/devices/virtual/hwmon/hwmon0/temp2_input = {'name':'Sensor 15','scaling':0.001,'triggers':{0:255}}
        ibm_thermal_sensor_0 = {'name':'CPU','triggers':{0:0, 40:2, 52:3, 60:255}}
        ibm_thermal_sensor_1 = {'name':'Sensor 1','triggers':{0:0, 40:2, 52:3, 60:255}}
        ibm_thermal_sensor_2 = {'name':'Sensor 2','triggers':{0:255}}
        ibm_thermal_sensor_3 = {'name':'Sensor 3','triggers':{0:0, 50:255}}
        ibm_thermal_sensor_4 = {'name':'Sensor 4','triggers':{0:0, 50:255}}
        ibm_thermal_sensor_5 = {'name':'Sensor 5','triggers':{0:255}}
        ibm_thermal_sensor_6 = {'name':'Sensor 6','triggers':{0:0, 50:255}}
        ibm_thermal_sensor_7 = {'name':'Sensor 7','triggers':{0:255}}
        ibm_thermal_sensor_8 = {'name':'Sensor 8','triggers':{0:0, 50:2, 60:255}}
        ibm_thermal_sensor_9 = {'name':'Sensor 9','triggers':{0:0, 50:255}}
        ibm_thermal_sensor_10 = {'name':'Sensor 10','triggers':{0:255}}
        ibm_thermal_sensor_11 = {'name':'Sensor 11','triggers':{0:255}}
        ibm_thermal_sensor_12 = {'name':'Sensor 12','triggers':{0:255}}
        ibm_thermal_sensor_13 = {'name':'Sensor 13','triggers':{0:255}}
        ibm_thermal_sensor_14 = {'name':'Sensor 14','triggers':{0:255}}
        ibm_thermal_sensor_15 = {'name':'Sensor 15','triggers':{0:255}}

* Here is an example ```profile_standard``` for a Thinkpad X201

	      # This file contains a fan profile for tpfancod
  	    [General]
	      # short description of the purpose of this profile.
	      comment =
	      # system manufacturer
	      product_vendor = LENOVO

        # thinkpad model
        product_name = ThinkPad X201

        # machine type
        product_id = 36805B8

        [Options]
        # set the hysteresis temperature difference.
        hysteresis = 2

        [Sensors]
        /sys/devices/virtual/hwmon/hwmon0/temp1_input = {'name':'CPU sensor','scaling':0.001,'triggers':{0:0, 40:1, 55:2, 60:255}}
			

* Here is an example of ```setting.conf```  
    
        # This file provides the general configuration of tpfancod

        [General]
        # set this to true to allow tpfancod control the fan of your machine.
        enabled = False
        # if a profile for your thinkpad model is available in the database,
        # tpfancod will use it by default and ignore any profiles you have
        # in /etc/tpfancod. set this to true to use custom profiles.
        override_profile = True
        # this determines the current custom profile used by tpfancod. the profile
        # must be placed in /etc/tpfancod and begin with profile_, e.g.
        # profile_library  or profile_gaming. this option works only if
        # override_profile is set to true.
        current_profile = profile_standard
    
  
  
# License 

tpfancod is covered by the GNU General Public License 3.

Copyright (C) 2011-2015 Vladyslav Shtabovenko  
Copyright (C) 2007-2009 Sebastian Urban

tpfancod is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

tpfancod is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with tpfancod. If not, see http://www.gnu.org/licenses/.


