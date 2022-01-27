from enum import Enum


# Message Labels <= 12 correspond to the v1 API.  > 12 correspond to v2 API
from typing import Optional

import serial

from DMXEnttecPro.utils import (
    least_significant_bit_for_size,
    most_significant_bit_for_size,
)


class Mk2MessageLabels(int, Enum):
    GET_PORT_WIDGET_PARAMETERS_REQUEST_REPLY_PORT1 = 3
    GET_PORT_WIDGET_PARAMETERS_REQUEST_REPLY_PORT2 = 196
    SET_PORT_WIDGET_PARAMETERS_REQUEST_PORT1 = 4
    SET_PORT_WIDGET_PARAMETERS_REQUEST_PORT2 = 156
    RECEIVED_DMX_PACKET_PORT1 = 5
    RECEIVED_DMX_PACKET_PORT2 = 210
    OUTPUT_ONLY_SEND_DMX_PACKET_REQUEST_PORT1 = 6
    OUTPUT_ONLY_SEND_DMX_PACKET_REQUEST_PORT2 = 132
    SEND_RDM_PACKET_REQUEST_PORT1 = 7
    SEND_RDM_PACKET_REQUEST_PORT2 = 226
    RECEIVE_DMX_ON_CHANGE_PORT1 = 8
    RECEIVE_DMX_ON_CHANGE_PORT2 = 128
    RECEIVED_DMX_CHANGE_OF_STATE_PACKET_PORT1 = 9
    RECEIVED_DMX_CHANGE_OF_STATE_PACKET_PORT2 = 22
    GET_WIDGET_SERIAL_NUMBER_REQUEST_REPLY = 10
    SEND_RDM_DISCOVERY_REQUEST_PORT1 = 11
    SEND_RDM_DISCOVERY_REQUEST_PORT2 = 208
    RDM_CONTROLLER_RECEIVE_TIMEOUT_PORT1 = 12
    RDM_CONTROLLER_RECEIVE_TIMEOUT_PORT2 = 209
    SET_API_KEY_REQUEST = 13
    QUERY_HARDWARE_VERSION_REQUEST_REPLY = 14
    GET_PORT_ASSIGNMENT_REQUEST_REPLY = 220
    SET_PORT_ASSIGNMENT_REQUEST = 201
    RECEIVED_MIDI = 225
    SEND_MIDI_REQUEST = 191
    SHOW_QUERY_REQUEST_REPLY = 139
    SHOW_BLOCK_ERASE_REQUEST = 129  # Distinguished by subcommand keyword "ERAS"
    SHOW_SECTOR_ERASE_REQUEST = 129  # Distinguished by subcommand keyword "ERSE"
    SHOW_WRITE_REQUEST = 129  # Distinguished by subcommand keyword "WRIT"
    SHOW_READ_REQUEST_REPLY = 203
    START_SHOW_REQUEST = 129  # Distinguished by subcommand keyword "STAR"
    STOP_SHOW_REQUEST = 129  # Distinguished by subcommand keyword "STOP"


class Mk2Controller(object):
    def __init__(
        self,
        port_string: str,
        dmx_size: int = 512,
        baudrate: int = 57600,
        timeout: int = 1,
        auto_submit: bool = False,
    ):
        if not (24 <= dmx_size <= 512):
            raise ValueError("Size of DMX channel frame must be between 24 and 512")
        self.dmx_size = dmx_size
        self.baudrate = baudrate
        self.timeout = timeout
        self.auto_submit = auto_submit

        self._conn = serial.Serial(
            port_string, baudrate=self.baudrate, timeout=self.timeout
        )

        self.channels = bytearray(self.dmx_size)
        self._last_submitted_channels = bytearray(self.dmx_size)
        self._signal_start = bytearray([0x7E])
        self._signal_end = bytearray([0xE7])

    def set_port_widget_parameters(
        self,
        *,
        port: int = 1,
        break_time: int = 9,
        mab_time: int = 1,
        rate: int = 40,
        user_defined_bytes: Optional[bytearray] = None,
    ):
        if user_defined_bytes is None:
            user_defined_bytes = bytearray()
        else:
            if len(user_defined_bytes) > 512:
                raise ValueError(
                    "Length of user_defined_bytes must not be greater than 512"
                )
        if port not in (1, 2):
            raise ValueError("port must be 1 or 2")
        if not (9 <= break_time <= 127):
            raise ValueError("output_break_time must be between 9 and 127")
        if not (1 <= mab_time <= 127):
            raise ValueError("mab_time must be between 1 and 127")
        if not (0 <= rate <= 40):
            raise ValueError("output_rate must be between 0 and 40")
        label = Mk2MessageLabels.SET_PORT_WIDGET_PARAMETERS_REQUEST_PORT1
        if port == 2:
            label = Mk2MessageLabels.SET_PORT_WIDGET_PARAMETERS_REQUEST_PORT2
        udb_len = len(user_defined_bytes)
        msg = (
            self._signal_start
            + bytearray(
                [
                    label.value,
                    least_significant_bit_for_size(udb_len + 5),
                    most_significant_bit_for_size(udb_len + 5),
                    least_significant_bit_for_size(udb_len),
                    most_significant_bit_for_size(udb_len),
                    break_time,
                    mab_time,
                    rate,
                ]
            )
            + user_defined_bytes
            + self._signal_end
        )
        self._conn.write(msg)
