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
from .transport import Protocol

class ProtocolV1(Protocol):

    def __init__(self, conn):
        Protocol.__init__(self)
        self.conn = conn
        self.conn.open()

    def close(self):
        self.conn.close()

    def _write(self, msg_type, data, datalen):
        header = struct.pack(">HL", msg_type, len(data))
        data = bytearray(b"##" + header + data)

        while len(data):
            buf = data[:63]
            chunk = b'?' + buf + b'\0' * (63 - len(buf))  # Report ID, data padded to 63 bytes
            self.conn.write_chunk(chunk)
            data = data[63:]

    def _read(self):
        chunk = self.conn.read_chunk()
        (msg_type, datalen, data) = self._parse_first(chunk)

        while len(data) < datalen:
            chunk = self.conn.read_chunk()
            data.extend(self._parse_next(chunk))

        data = data[:datalen]  # Strip padding zeros
        return (0, msg_type, data)

    def _parse_first(self, chunk):
        if chunk[:3] != b"?##":
            raise Exception("Unexpected magic characters")
        try:
            headerlen = struct.calcsize(">HL")
            (msg_type, datalen) = struct.unpack(">HL", bytes(chunk[3:3 + headerlen]))
        except:
            raise Exception("Cannot parse header")
        data = chunk[3 + headerlen:]
        return (msg_type, datalen, data)

    def _parse_next(self, chunk):
        if chunk[0:1] != b"?":
            raise Exception("Unexpected magic characters")
        return chunk[1:]
