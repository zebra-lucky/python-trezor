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

class Device(object):

    def __init__(self, path):
        self.path = path
        self.conn = None
        self.conn_debug = None
        self.protocol = None

    @staticmethod
    def enumerate():
        raise NotImplementedError()

    def open(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def _write_chunk(self, chunk):
        raise NotImplementedError()

    def _read_chunk(self):
        raise NotImplementedError()

    def _read(self, msg, conn):
        pass

    def _write(self, msg, conn):
        pass

    def read(self, msg):
        return self._read(msg, self.conn)

    def read_debug(self, msg):
        return self._read(msg, self.conn_debug)

    def write(self, msg):
        return self._write(msg, self.conn)

    def write_debug(self, msg):
        return self._write(msg, self.conn_debug)
