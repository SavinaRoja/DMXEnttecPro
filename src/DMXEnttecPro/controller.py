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
    """
    def __init__(self,
                 port_string: str,
                 dmx_size: int = 512,
                 baudrate: int = 57600,
                 timeout: int = 1,
                 auto_submit: bool = False
                 ):
        """
        Instantiate Controller

        Arguments:
        :param port_string: COM port to use for communication
        :param dmx_size: Number of channels form 24 to 512 [default: 512]
        :param baudrate: Baudrate for serial connection [default: 57600]
        :param timeout: Serial connection timeout [default: 1]
        :param auto_submit: Enable or disable default automatic submission
                   [default: False]
        """

        if not(24 <= dmx_size <= 512):
            raise ValueError('Size of DMX channel frame must be between 24 and 512')
        self.dmx_size = dmx_size
        self.baudrate = baudrate
        self.timeout = timeout
        self.auto_submit = auto_submit

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

    def set_dmx_parameters(self,
                           output_break_time: int = 9,
                           mab_time: int = 1,
                           output_rate: int = 40,
                           user_defined_bytes=None):
        """
        Transmit a message to the Enttec DMX USB Pro to configure some
        timing aspects of the DMX signal. See the details below:

        :param output_break_time:  Sets the Break time interval for the DMX
            packets. Integers between 9 and 127 are accepted per Enttec
            documentation. A base unit of 10.67 microseconds is used, so the
            resulting break time will be 10.67 * output_break_time microseconds.
        :param mab_time:  Sets the MAB (Mark After Break) time interval for the
            DMX packets. Integers between 1 and 127 are accepted per Enttec
            documentation. A base unit of 10.67 microseconds is used, so the
            resulting break time will be 10.67 * output_break_time microseconds.
        :param output_rate:  Set the rate of DMX Packet sending. Integers
            between 0 and 40 are accepted. 1 through 40 will set the rate in Hz.
            0 is a special value, causing the packets to be sent as fast as
            possible by setting the time between packets to 0. Maximum send
            rate is a function of packet size, calculable by this function:
              1000000/((output_break_time * 10.67) + (mab_time * 10.67) +
                       ((dmx_size + 1) * 44))
        :param user_defined_bytes: The Enttec DMX USB Pro documentation allows
            for user-defined data to also be transmitted. This is likely only
            relevant to special firmware on the device. Accepts bytearrays of
            length 0 to 512.
        :return:
        """
        if user_defined_bytes is None:
            user_defined_bytes = bytearray()
        else:
            if len(user_defined_bytes) > 512:
                raise ValueError(
                    'Length of user_defined_bytes must not be greater than 512')
        if not (9 <= output_break_time <= 127):
            raise ValueError('output_break_time must be between 9 and 127')
        if not (1 <= mab_time <= 127):
            raise ValueError('mab_time must be between 1 and 127')
        if not (0 <= output_rate <= 40):
            raise ValueError('output_rate must be between 0 and 40')
        msg = (self._signal_start +
               bytearray([4,  # Set Widget Parameters Request
                          (len(user_defined_bytes) + 1) & 0xFF,  # user defined length LSB
                          ((len(user_defined_bytes) + 1) >> 8) & 0xFF,  # user defined length MSB
                          output_break_time,
                          mab_time,
                          output_rate,
                          ]) +
               user_defined_bytes +
               self._signal_end
               )
        self._conn.write(msg)

    def submit(self):
        """
        Submit the channel state to the DMX Device over serial.
        """

        msg = (self._signal_start +
               bytearray([6,  # Output Only Send DMX Packet Request
                          (len(self.channels) + 1) & 0xFF,  # Data length LSB
                          ((len(self.channels) + 1) >> 8) & 0xFF,  # Data length MSB
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
