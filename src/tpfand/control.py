#! /usr/bin/env python
# -*- coding: utf8 -*-
#
# tp-fancontrol - controls the fan-speed of IBM/Lenovo ThinkPad Notebooks
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

import sys, os, os.path, time, signal
import dbus, dbus.service, dbus.mainloop.glib, dbus.glib
import gobject

from tpfand import build, settings

IBM_fan = '/proc/acpi/ibm/fan'
IBM_thermal = '/proc/acpi/ibm/thermal'

#debug
debug = False

# Configuration
act_settings = None

# Fan controller
controller = None

class UnavailableException(dbus.DBusException):
    _dbus_error_name = "org.thinkpad.fancontrol.UnavailableException"    

class Control(dbus.service.Object):
    """fan controller"""
    
    # poll time
    poll_time = 3500
    # kernel watchdog time
    # the thinkpad_acpi watchdog accepts intervals between 1 and 120 seconds
    # for safety reasons one shouldn't use values higher than 5 seconds        
    watchdog_time = 5    
    # value that temperature has to fall below to slow down fan  
    current_trip_temps = { }
    # current fan speeds required by sensor readings
    current_trip_speeds = { }
    # last spinup time for interval cooling mode    
    last_interval_spinup = 0
    # fan in interval cooling mode
    #interval_mode = False
    # fan on in interval cooling mode
    #interval_running = False        

    def __init__(self, bus, path):
        dbus.service.Object.__init__(self, bus, path)
        self.repoll(1)
    
    def set_speed(self, speed):
        """sets the fan speed (0=off, 2-8=normal, 254=disengaged, 255=ec, 256=full-speed)"""
        fan_state = self.get_fan_state()
        try:
            if debug:
                print '  Rearming fan watchdog timer (+' + str(self.watchdog_time) + ' s)'
                print '  Current fan level is ' + str(fan_state['level'])
            fanfile = open(IBM_fan, 'w')
            fanfile.write("watchdog %d" % self.watchdog_time)
            fanfile.flush()            
            if speed == fan_state['level']:
                if debug:
                    print '  -> Keeping the current fan level unchanged'
            else:
                if debug:
                    print '  -> Setting fan level to ' + str(speed)
                if speed == 0:
                    fanfile.write('disable')
                else:
                    fanfile.write('enable')
                    fanfile.flush()
                    if speed == 254:
                        fanfile.write("level disengaged")
                    if speed == 255:
                        fanfile.write("level auto")
                    elif speed == 256:
                        fanfile.write("level full-speed")
                    else:
                        fanfile.write("level %d" % (speed - 1))
            fanfile.flush()            
        except IOError:
            # sometimes write fails during suspend/resume
            pass
        finally:
            try:
                fanfile.close()
            except:
                pass    

    @dbus.service.method("org.thinkpad.fancontrol.Control", in_signature='', out_signature='s')         
    def get_version(self):
        return build.version
    
    @dbus.service.method('org.thinkpad.fancontrol.Control', in_signature='', out_signature='ai')
    def get_temperatures(self):
        """returns list of current sensor readings, +/-128 or 0 means sensor is disconnected"""
        try:
            tempfile = open(IBM_thermal, 'r')
            elements = tempfile.readline().split()[1:]
            tempfile.close()
            return map(int, elements)
        except IOError, e:
            # sometimes read fails during suspend/resume        
            raise UnavailableException(e.message)
        finally:
            try:
                tempfile.close()
            except:
                pass
        
    @dbus.service.method('org.thinkpad.fancontrol.Control', in_signature='', out_signature='a{si}')
    def get_fan_state(self):
        """Returns current (fan_level, fan_rpm)"""
        try:
            fanfile = open(IBM_fan, 'r')
            for line in fanfile.readlines():
                key, value = line.split(':')
                if key == 'speed':
                    rpm = int(value.strip())
                if key == 'level':
                    value = value.strip()
                    if value == '0':
                        level = 0
                    elif value == 'auto':
                        level = 255
                    elif value == 'disengaged' or value == 'full-speed':
                        level = 256
                    #Ugly stub for the removed interval mode
                    elif value == 1:
                        level = 2
                    else:
                        level = int(value) + 1 
            #if act_settings.enabled and self.interval_mode:
            #    level = 1
            return {'level': level,
                    'rpm': rpm }
        except Exception, e:
            raise UnavailableException(e.message)
        finally:
            try:
                fanfile.close()
            except:
                pass
            
    @dbus.service.method('org.thinkpad.fancontrol.Control', in_signature='', out_signature='')            
    def reset_trips(self):
        """resets current trip points, should be called after config change"""
        self.current_trip_speeds = { }
        self.current_trip_temps = { }  
        
    @dbus.service.method('org.thinkpad.fancontrol.Control', in_signature='', out_signature='a{ii}')
    def get_trip_temperatures(self):      
        """returns the current hysteresis temperatures for all sensors"""
        return self.current_trip_temps
    
    @dbus.service.method('org.thinkpad.fancontrol.Control', in_signature='', out_signature='a{ii}')
    def get_trip_fan_speeds(self):      
        """returns the current hysteresis fan speeds for all sensors"""
        return self.current_trip_speeds    

    def repoll(self, interval):
        """calls poll again after interval msecs"""
        ival = int(interval)
        # ensure limits
        # i.e. make sure that we always repoll before the watchdog timer runs out        
        if ival < 1: 
            ival = 1
        if ival > self.watchdog_time * 1000:
            ival = self.watchdog_time * 1000
        
        gobject.timeout_add(ival, self.poll)
            
    def poll(self):
        """main fan control routine"""
        # get the current fan level
        fan_state = self.get_fan_state()
        
        if debug:
              print
              print str(time.strftime("%H:%M:%S")) + ': Polling the sensors'
              print 'Current fan level: ' + str(fan_state['level']) + ' (' + str(fan_state['rpm']) + ' RPM)'
       
        if act_settings.enabled:
            # early interval shutdown
            #curtime = time.time() * 1000.0
            #if self.interval_running and curtime >= self.last_interval_spinup + act_settings.interval_duration:
            #    self.set_speed(0)
                        
            # probing the disengaged mode
            #if level not in (0,1,254,255,256):
            #    if debug:
            #      print 'Applying fan pulsing fix'
            #    self.set_speed(254)
            #    time.sleep(0.5)
            #    self.set_speed(level)
                        
            # read thermal data
            try:
                temps = self.get_temperatures()
            except UnavailableException:
                # temperature read failed
                self.set_speed(255)
                self.repoll(self.poll_time)
                return False

            new_speed = 0
            if debug:
                        print 'Current sensor values:'
            for id in range(0, len(temps)):
                temp = temps[id]                
                # value is +/-128 or 0, if sensor is disconnected
                if abs(temp) != 128 and abs(temp) != 0:
                    points = act_settings.trigger_points[id]                    
                    speed = 0
                    
                    if debug:                        
                        print '    Sensor ' + str(id) +': ' + str(temp)
                    
                    # check if temperature is above hysteresis shutdown point
                    if id in self.current_trip_temps:
                        if temp >= self.current_trip_temps[id]:
                            speed = self.current_trip_speeds[id]
                        else:
                            del self.current_trip_temps[id]
                            del self.current_trip_speeds[id]
                            
                    # check if temperature is over trigger point
                    for trigger_temp, trigger_speed in points.iteritems():
                        if temp >= trigger_temp and speed < trigger_speed:
                            self.current_trip_temps[id] = trigger_temp - act_settings.hysteresis
                            self.current_trip_speeds[id] = trigger_speed
                            speed = trigger_speed
                    
                    new_speed = max(new_speed, speed)                                            
            if debug:
                print 'Trying to set fan level to ' + str(new_speed) + ':'
                
            # set fan speed
            #if new_speed == 1:
            #    # handle interval mode
            #    self.interval_mode = True
            #    curtime = time.time() * 1000.0
            #    if self.interval_running:
            #        if curtime >= self.last_interval_spinup + act_settings.interval_duration:
            #            self.set_speed(0)
            #            self.interval_running = False
            #            self.repoll(min(self.poll_time, act_settings.interval_delay))
            #        else:
            #            self.set_speed(act_settings.interval_speed)
            #            self.repoll(max(0, min(self.poll_time, self.last_interval_spinup + act_settings.interval_duration - curtime)))
            #    else:
            #        if curtime >= self.last_interval_spinup + act_settings.interval_duration + act_settings.interval_delay:
            #            self.last_interval_spinup = curtime
            #            self.set_speed(act_settings.interval_speed)
            #            self.interval_running = True
            #            self.repoll(min(self.poll_time, act_settings.interval_duration))
            #        else:
            #            self.set_speed(0)
            #            self.repoll(max(0, min(self.poll_time, self.last_interval_spinup + act_settings.interval_duration + act_settings.interval_delay - curtime)))
            #else:
                # handle normal fan mode
            #    self.interval_mode = False
            #    self.interval_running = False
            self.set_speed(new_speed)      
            self.repoll(self.poll_time)
        else:
            # fan control disabled
            self.set_speed(255)
            self.repoll(self.poll_time)
        
        # remove current timer
        return False
             
def daemon_main():
    """daemon entry point"""  
    global controller, mainloop, act_settings  
     
    # register SIGTERM handler
    signal.signal(signal.SIGTERM, term_handler)    
    
    # register d-bus service
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    system_bus = dbus.SystemBus()
    name = dbus.service.BusName("org.thinkpad.fancontrol.tpfand", system_bus)

    # create and load configuration
    act_settings = settings.Settings(system_bus, '/Settings')

    # create controller
    controller = Control(system_bus, '/Control')                  

    # start glib main loop          
    mainloop = gobject.MainLoop()  
    mainloop.run()  

def term_handler(signum, frame):
    """Handles SIGTERM"""
    controller.set_speed(255)
    try:
        os.remove(build.pid_path)
    except:
        pass    
    mainloop.quit()        
         
def is_system_suitable():
    """returns True iff fan speed setting, watchdog and thermal reading is supported by kernel and 
       we have write permissions"""
    try:
        fanfile = open(IBM_fan, 'w')
        fanfile.write('level auto')
        fanfile.flush()
        fanfile.close()
        fanfile = open(IBM_fan, 'w')
        fanfile.write('watchdog 5')
        fanfile.flush()
        fanfile.close()
        
        tempfile = open(IBM_thermal, 'r')
        tempfile.readline()
        tempfile.close()
        return True
    except IOError:
        return False         
         
def start_fan_control(quiet):
    """daemon start function"""
    
    if not quiet:
        print 'tpfand ' + build.version + ' - Copyright (C) 2007-2008 Sebastian Urban'
        print 'This program comes with ABSOLUTELY NO WARRANTY'
        print
        print 'WARNING: THIS PROGRAM MAY DAMAGE YOUR COMPUTER.'
        print '         PROCEED ONLY IF YOU KNOW HOW TO MONITOR SYSTEM TEMPERATURE.'
        print
               
    if debug:
        print 'Running in debug mode'
    
    if not is_system_suitable():
        print "Fatal error: unable to set fanspeed, enable watchdog or read temperature"
        print "             Please make sure you are root and a recent"
        print "             thinkpad_acpi module is loaded with fan_control=1"
        exit(1)
        
    if os.path.isfile(build.pid_path):
        print "Fatal error: already running or " + build.pid_path + " left behind"
        exit(1)
                   
    # go into daemon mode
    daemonize()
    
def daemonize():
    """ don't go into daemon mode if debug mode is active """
    if not debug:
        """go into daemon mode"""   
        # from: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
        # do the UNIX double-fork magic, see Stevens' "Advanced 
        # Programming in the UNIX Environment" for details (ISBN 0201563177)
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit first parent
                sys.exit(0) 
        except OSError, e: 
            print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror) 
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/") 
        os.setsid() 
        os.umask(0) 

        # do second fork
        try: 
            pid = os.fork() 
            if pid > 0:
                sys.exit(0) 
        except OSError, e: 
            print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror) 
            sys.exit(1) 

        # write pid file
        try:
            pidfile = open(build.pid_path, 'w')
            pidfile.write(str(os.getpid()) + "\n")
            pidfile.close()
        except IOError:
            print >>sys.stderr, "could not write pid-file: ", build.pid_path
            sys.exit(1)
    
    # start the daemon main loop
    daemon_main()   
    
    
def main():
    quiet = False
    global debug
    
    if "--quiet" in sys.argv:
        quiet = True
    
    if "--debug" in sys.argv:
        debug = True
        
    start_fan_control(quiet)     

if __name__ == "__main__":
    main()
    
