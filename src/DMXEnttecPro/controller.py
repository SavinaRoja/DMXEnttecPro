# coding: utf-8

"""
Defines the Controller
"""

import serial
from functools import wraps


class Controller(object):
    """
    Controller maintains a state and interface for interacting with the Enttec
    DMX USB Pro.

    Key methods include:
      `set_channel(channel, value)` - Sets channel to value
      `submit()` - Send state to device
      `close()` - Close serial connection to device

    Convenience methods:
      `clear_channels()` - Sets all channels to 0
      `all_channels_on()` -  Sets all channels to 255
      `set_all_channels(value)` - Sets all channels to value

    Automatic submission of state changes configurable with `auto_submit`
    argument. Usage of `submit_after` argument in state-changing methods takes
    precedence over this default.

    Dynamic submission of state configurable with `dynamic_submit` argument.
    Dynamic submission sends only as many channels as necessary over serial
    to fully update the Enttec device. When disabled, submission sends all
    channels every time. Using this can enable updates to transmit more rapidly.
    """
    def __init__(self,
                 port_string: str,
                 dmx_size: int = 512,
                 baudrate: int = 57600,
                 timeout: int = 1,
                 auto_submit: bool = False,
                 dynamic_submit: bool = False):
        """
        Instantiate Controller

        Arguments:
        :param port_string: COM port to use for communication
        :param dmx_size: Number of channels form 24 to 512 [default: 512]
        :param baudrate: Baudrate for serial connection [default: 57600]
        :param timeout: Serial connection timeout [default: 1]
        :param auto_submit: Enable or disable default automatic submission
                   [default: False]
        :param dynamic_submit: Enable or disable dynamic submission
                   [default: False]
        """

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

        :return: method wrapped in auto submission behavior
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

    def _get_minimal_submission(self) -> bytearray:
        """
        Computes minimum number of channels to submit to submit all changes
        not yet submitted to the device.

        :return: bytearray subset of self.channels
        """
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
        """
        Sets all channels to 0.

        :param submit_after:  Pass True to submit DMX state after completion.
                              False to not submit, overriding self.auto_submit.
        :return:
        """
        self.channels = bytearray(self.dmx_size)

    @_auto_submit
    def set_all_channels(self, value: int):
        """
        Set all channel values in the DMX channel bytearray.

        :param submit_after:  Pass True to submit DMX state after completion.
            False to not submit, overriding self.auto_submit.
        :param value: Integer from 1 to 512
        """
        self.channels = bytearray([value]*self.dmx_size)

    @_auto_submit
    def all_channels_on(self):
        """
        Set all channels to 255.

        :param submit_after:  Pass True to submit DMX state after completion.
            False to not submit, overriding self.auto_submit.
        :return:
        """
        self.channels = bytearray([255]*self.dmx_size)

    @_auto_submit
    def set_channel(self, channel: int, value: int):
        """
        Set a channel value in the DMX channel bytearray.

        :param channel: Integer from 1 to 512
        :param value: Integer from 0 to 255
        :param submit_after:  Pass True to submit DMX state after completion.
            False to not submit, overriding self.auto_submit.
        :return:
        """
        self.channels[channel-1] = value

    def get_channel(self, channel: int) -> int:
        """
        Returns the value of a channel.

        :param channel: Integer from 1 to 512
        :return: Integer from 0 to 255
        """
        return self.channels[channel-1]

    def close(self):
        """
        Closes the serial connection nicely. Should be used before creating a
        new Controller instance on the same COM port.

        :return:
        """
        self._conn.close()
