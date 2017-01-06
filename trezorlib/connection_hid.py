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

'''USB HID implementation of Connection.'''

import hid
import time
from .transport_v1 import TransportV1
from .transport_v2 import TransportV2

DEVICE_IDS = [
    (0x534c, 0x0001),  # TREZOR
    (0x1209, 0x53C0),  # TREZORv2 Bootloader
    (0x1209, 0x53C1),  # TREZORv2
]

DEVICE_TRANSPORTS = {
    (0x534c, 0x0001): TransportV1,  # TREZOR
    (0x1209, 0x53C0): TransportV2,  # TREZORv2 Bootloader
    (0x1209, 0x53C1): TransportV2,  # TREZORv2
}

def device_to_transport(device):
    try:
        transport = DEVICE_TRANSPORTS[(device['vendor_id'], device['product_id'])]
    except IndexError:
        raise Exception("Unknown transport for %s" % device)
    return transport

class HidConnection(object):
    def __init__(self, device, hid_version=None):
        self.path = device['path']
        self.hid_version = hid_version  # None, 1, 2
        self.hid = None

    @staticmethod
    def enumerate():
        """
        Return a list of available TREZOR devices as a list of tuples.  First item is the normal
        interface, second item is the debug interface.
        """
        devices = {}
        for d in hid.enumerate(0, 0):
            vendor_id = d['vendor_id']
            product_id = d['product_id']
            serial_number = d['serial_number']
            interface_number = d['interface_number']
            usage_page = d['usage_page']

            if (vendor_id, product_id) in DEVICE_IDS:
                devices.setdefault(serial_number, [None, None])
                # first match by usage_page, then try interface number
                if usage_page == 0xFF00 or interface_number == 0:  # normal link
                    devices[serial_number][0] = d
                elif usage_page == 0xFF01 or interface_number == 1:  # debug link
                    devices[serial_number][1] = d
        return sorted(devices.values())

    def is_connected(self):
        """
        Check if the device is still connected.
        """
        for d in hid.enumerate(0, 0):
            if d['path'] == self.path:
                return True
        return False

    def open(self):
        if self.hid:
            return
        self.hid = hid.device()
        self.hid.open_path(self.path)
        self.hid.set_nonblocking(True)

        if self.hid_version is None:
            r = self.hid.write([0, 63, ] + [0xFF] * 63)
            if r == 65:
                self.hid_version = 2
                return
            r = self.hid.write([63, ] + [0xFF] * 63)
            if r == 64:
                self.hid_version = 1
                return
            raise ConnectionError("Unknown HID version")

    def close(self):
        if not self.hid:
            return
        self.hid.close()
        self.hid = None

    def write_chunk(self, chunk):
        if len(chunk) != 64:
            raise Exception("Unexpected data length")

        if self.hid_version == 2:
            self.hid.write(b'\0' + chunk)
        else:
            self.hid.write(chunk)

    def read_chunk(self):
        start = time.time()

        while True:
            data = self.hid.read(64)
            if not len(data):
                if time.time() - start > 10:
                    # Over 10 s of no response, let's check if device is still alive
                    if not self.is_connected():
                        raise ConnectionError("Connection failed")

                    # Restart timer
                    start = time.time()

                time.sleep(0.001)
                continue

            break

        if len(data) != 64:
            raise Exception("Unexpected chunk size: %d" % len(data))

        return bytearray(data)
