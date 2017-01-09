# This file is part of the TREZOR project.
#
# Copyright (C) 2012-2016 Marek Palatinus <slush@satoshilabs.com>
# Copyright (C) 2012-2016 Pavol Rusnak <stick@satoshilabs.com>
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import sys
sys.path = ['../../'] + sys.path

from trezorlib.transport_hid import HidTransport
from trezorlib.transport_udp import UdpTransport

devices = HidTransport.enumerate()

if len(devices) > 0:
    print('Using TREZOR')
    TRANSPORT = HidTransport
    TRANSPORT_ARGS = (devices[0],)
    TRANSPORT_KWARGS = {'debug_link': False}
    DEBUG_TRANSPORT = HidTransport
    DEBUG_TRANSPORT_ARGS = (devices[0],)
    DEBUG_TRANSPORT_KWARGS = {'debug_link': True}

elif True:
    print('Using Emulator (v2=udp)')
    TRANSPORT = UdpTransport
    TRANSPORT_ARGS = ('', )
    TRANSPORT_KWARGS = {}
    DEBUG_TRANSPORT = UdpTransport
    DEBUG_TRANSPORT_ARGS = ('', )
    DEBUG_TRANSPORT_KWARGS = {}
