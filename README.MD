# Warning

The code in this repository is not yet ready for productive use!
Use it on your own risk!

# Tpfanco daemon (tpfancod)

tpfancod controls the system fan of ThinkPad notebooks based on specified
temperature profiles. Seperate trigger points can be configured for every
temperature sensor in the notebook.

tpfancod is written entirely in Python and licensed under the GNU GPL version 3.

# Requirements

* Python 2.7
* DBus with bindings for Python
* thinkpad_acpi kernel module loaded with fan_control=1 to enable fan control.

# Installation

Pacakges for the development version are currently not available. The following
sections describe manual installation via `make`

## systemd based distributions

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
## sysvinit based distributions

* Run
    ```
    sudo make install-sysvinit
    ```

* Reboot your system to reload `thinkpad_acpi` module with the
  `fan_control=1`option.

# Uninstall

* You can uninstall tpfancod by running

    ```
    sudo make uninstall
    ```

# Configuration

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

  ```
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

  ```

* And here is an example for a Thinkpad X201

# This file contains a fan profile for tpfancod

  ```
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
  ```

* Currently tpfanco-admin doesn't work with tpfancod


