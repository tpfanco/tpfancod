#! /usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# tpfanco - controls the fan-speed of IBM/Lenovo ThinkPad Notebooks
# Copyright (C) 2011-2012 Vladyslav Shtabovenko
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

import sys
if not ('/usr/share/pyshared' in sys.path):
    sys.path.append('/usr/share/pyshared')

# data directory
data_dir = "/usr/share/tpfand/"

# path to config file
config_path = "/etc/tpfand.conf"

# path to pid file
pid_path = "/var/run/tpfand.pid"

# version
version = "0.95.3"

