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

from . import mapping

class Protocol(object):

    def __init__(self):
        self.session_id = 0
        self.session_depth = 0

    def session_begin(self):
        """
        Apply a lock to the device in order to preform synchronous multistep "conversations"
        with the device.  For example, before entering the transaction signing workflow, one
        begins a session.  After the transaction is complete, the session may be ended.
        """
        if self.session_depth == 0:
            self._session_begin()
        self.session_depth += 1

    def session_end(self):
        """
        End a session.  See session_begin for an in depth description of TREZOR sessions.
        """
        self.session_depth -= 1
        self.session_depth = max(0, self.session_depth)
        if self.session_depth == 0:
            self._session_end()

    def write(self, msg):
        """
        Write message to transport.  msg should be a member of a valid protobuf instance with a
        SerializeToString() method.
        """
        msg_type = mapping.get_type(msg)
        msg_data = msg.SerializeToString()
        self._write(msg_type, msg_data, len(msg_data))

    def read(self):
        """
        If there is data available to be read from the transport, reads the data and tries to
        parse it as a protobuf message.  If the parsing succeeds, return a protobuf object.
        Otherwise, returns None.
        """
        data = self._read()
        if data is None:
            return None
        return self._parse_message(data)

    def read_blocking(self):
        """
        Same as read, except blocks until data is available to be read.
        """
        while True:
            data = self._read()
            if data != None:
                break
        return self._parse_message(data)

    def _parse_message(self, data):
        (session_id, msg_type, data) = data

        # Raise exception if we get the response with unexpected session ID
        if session_id != self.session_id:
            raise Exception("Session ID mismatch. Have %d, got %d" % (self.session_id, session_id))

        if msg_type == 'protobuf':
            return data
        else:
            inst = mapping.get_class(msg_type)()
            inst.ParseFromString(bytes(data))
            return inst

    # Required transport virtual methods:

    def _write(self, msg_type, data, datalen):
        raise NotImplementedError()

    def _read(self):
        raise NotImplementedError()

    # Optional transport virtual methods:

    def _session_begin(self):
        pass

    def _session_end(self):
        pass

    def close(self):
        pass
