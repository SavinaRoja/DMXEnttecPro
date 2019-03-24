# coding: utf-8

"""
Defines the Controller
"""

import serial
from functools import wraps


class Controller(object):

    def __init__(self,
                 port_string: str,
                 dmx_size: int = 512,
                 baudrate: int = 57600,
                 timeout: int = 1,
                 auto_submit: bool = False,
                 dynamic_submit: bool = False):

        if not(24 <= dmx_size <= 512):
            raise ValueError('Size of DMX channel frame must be between 24 and 512')
        self.dmx_size = dmx_size
        self.baudrate = baudrate
        self.timeout = timeout
        self.auto_submit = auto_submit
        self.dynamic_submit = dynamic_submit

        self._conn = serial.Serial(
            port_string,
            baudrate=self.baudrate,
            timeout=self.timeout
            )

        self.channels = bytearray(self.dmx_size)
        self._last_submitted_channels = bytearray(self.dmx_size)
        self._signal_start = bytearray([0x7E])
        self._signal_end = bytearray([0xE7])

    def _auto_submit(f):
        """
        This decorator encloses a method with the auto submission behavior as
        configured by the DMX instance's `auto_submit` attribute and the
        `submit_after` keyword argument. Both of these should be boolean where
        `True` indicates automatic serial submission after the wrapped method.

        If `submit_after` is supplied as not `None`. Then it takes precedence
        over `self.auto_submit`. Otherwise `self.auto_submit` is used.
        :return:
        """
        @wraps(f)
        def wrapper(self, *args, submit_after=None, **kwargs):
            f(self, *args, **kwargs)  # call the wrapped method
            if submit_after is None:
                if self.auto_submit:
                    self.submit()

            elif submit_after:
                self.submit()
        return wrapper

    def _get_minimal_submission(self):
        for i, (v0, v1) in enumerate(zip(reversed(self.channels),
                                         reversed(self._last_submitted_channels))):
            if v0 != v1:
                return self.channels[:self.dmx_size-i]
        return bytearray()

    def submit(self):
        """
        Submit the channel state to the DMX Device over serial.
        """
        if self.dynamic_submit:
            channels = self._get_minimal_submission()
            if len(channels) == 0:
                return
            elif len(channels) <= 24:
                channels = self.channels[:24]
        else:
            channels = self.channels

        msg = (self._signal_start +
               bytearray([6,  # Output Only Send DMX Packet Request
                          (len(channels) + 1) & 0xFF,  # Data length LSB
                          ((len(channels) + 1) >> 8) & 0xFF,  # Data length MSB
                          0]) +
               self.channels +
               self._signal_end
               )
        self._conn.write(msg)
        self._last_submitted_channels = self.channels.copy()

    @_auto_submit
    def clear_channels(self):
        self.channels = bytearray(self.dmx_size)

    @_auto_submit
    def set_all_channels(self, value: int):
        """
        Set all channel values in the DMX channel bytearray.
        :param value:
        """
        self.channels = bytearray([value]*self.dmx_size)

    @_auto_submit
    def all_channels_on(self):
        self.channels = bytearray([255]*self.dmx_size)

    @_auto_submit
    def set_channel(self, channel: int, value: int):
        """
        Set a channel value in the DMX channel bytearray.
        :param channel:
        :param value:
        """
        self.channels[channel-1] = value

    def get_channel(self, channel: int):
        """
        Returns the value of a channel.
        :param channel:
        :return: integer value
        """
        return self.channels[channel-1]

    def close(self):
        self._conn.close()
