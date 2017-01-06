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

import struct
import binascii
from .transport import Transport

class TransportV2(Transport):
    def __init__(self, conn):
        Transport.__init__(self)
        self.conn = conn
        self.conn.open()

    def close(self):
        self.conn.close()

    def _write(self, msg_type, data, datalen):
        if not self.session_id:
            raise Exception("Missing session_id for v2 transport")

        data = bytearray(data)
        checksum = binascii.crc32(data) & 0xffffffff  # Convert to unsigned in python2

        header1 = struct.pack(">L", self.session_id)
        header2 = struct.pack(">LL", msg_type, datalen)
        footer = struct.pack(">L", checksum)

        data = header2 + data + footer

        first = True
        while len(data):
            if first:
                # Magic character, header1, header2, data padded to 64 bytes
                datalen = 63 - len(header1)
                chunk = b'H' + header1 + \
                    data[:datalen] + b'\0' * (datalen - len(data[:datalen]))
            else:
                # Magic character, header1, data padded to 64 bytes
                datalen = 63 - len(header1)
                chunk = b'D' + header1 + \
                    data[:datalen] + b'\0' * (datalen - len(data[:datalen]))

            self.conn.write_chunk(chunk)
            data = data[datalen:]
            first = False

    def _read(self):
        if not self.session_id:
            raise Exception("Missing session_id for v2 transport")

        chunk = self.conn.read_chunk()
        (session_id, msg_type, datalen, data) = self._parse_first(chunk)
        payloadlen = datalen + 4  # For the checksum

        while len(data) < payloadlen:
            chunk = self.conn.read_chunk()
            (next_session_id, next_data) = self._parse_next(chunk)

            if next_session_id != session_id:
                raise Exception("Session id mismatch")

            data.extend(next_data)

        data = data[:payloadlen]  # Strip padding zeros
        footer = data[-4:]
        data = data[:-4]

        csum, = struct.unpack('>L', footer)
        csum_comp = binascii.crc32(data) & 0xffffffff
        if csum != csum_comp:
            raise Exception("Message checksum mismatch. Expected %d, got %d" % (csum_comp, csum))

        return (session_id, msg_type, data)

    def _parse_first(self, chunk):
        if chunk[0:1] != b"H":
            raise Exception("Unexpected magic character")
        try:
            headerlen = struct.calcsize(">LLL")
            (session_id, msg_type, datalen) = struct.unpack(">LLL", bytes(chunk[1:1 + headerlen]))
        except:
            raise Exception("Cannot parse header")
        return (session_id, msg_type, datalen, chunk[1 + headerlen:])

    def _parse_next(self, chunk):
        if chunk[0:1] != b"D":
            raise Exception("Unexpected magic characters")
        try:
            headerlen = struct.calcsize(">L")
            (session_id,) = struct.unpack(">L", bytes(chunk[1:1 + headerlen]))
        except:
            raise Exception("Cannot parse header")
        return (session_id, chunk[1 + headerlen:])

    def _session_begin(self):
        chunk_open = bytearray(b'O' + b'\0' * 63)
        self.conn.write_chunk(chunk_open)
        chunk_ack = self.conn.read_chunk()
        if chunk_ack[0] != ord('O'):
            raise Exception("Expected session open")
        self.session_id = self._parse_session_open(chunk_ack)

    def _session_end(self):
        header = struct.pack(">L", self.session_id)
        chunk_close = bytearray(b'C' + header + b'\0' * (63 - len(header)))
        self.conn.write_chunk(chunk_close)
        chunk_ack = self.conn.read_chunk()
        if chunk_ack[0] != ord('C'):
            raise Exception("Expected session close")
        self.session_id = None

    def _parse_session_open(self, chunk):
        if chunk[0:1] != b"O":
            raise Exception("Unexpected magic character")
        try:
            headerlen = struct.calcsize(">L")
            (session_id,) = struct.unpack(">L", bytes(chunk[1:1 + headerlen]))
        except:
            raise Exception("Cannot parse header")
        return session_id
