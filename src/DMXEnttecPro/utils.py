# coding: utf-8

"""
DMXEnttecPro.utils defines some helpful functions for working with serial
devices. Module can be executed as script via `python -m DMXEnttecPro.utils`
which executes `show_port_details()` to print information about all connected
COM ports.
"""

import serial.tools.list_ports as slp


# Important docs: https://pyserial.readthedocs.io/en/latest/tools.html
def get_port_by_serial_number(serial_number: str) -> str:
    """
    Tries to find a COM port that matches the serial number given

    :param serial_number: serial number, string
    :return: COM port name, string
    """
    all_ports = slp.comports()
    for port in all_ports:
        if port.serial_number == serial_number:
            return port.device
    # No port could be found for the serial number
    raise ValueError('No COM device found with serial {}'.format(serial_number))


def get_port_by_product_id(product_id: int) -> str:
    """
    Tries to find a COM port that matches the product ID given.

    :param product_id: Product ID, integer
    :return: COM port name, string
    """
    all_ports = slp.comports()
    for port in all_ports:
        if port.pid == product_id:
            return port.device
    # No port could be found for the serial number
    raise ValueError('No COM device found with product id {}'.format(product_id))


def show_port_details():
    """
    Print a listing of all COM ports PySerial can find. Useful for determining
    which COM port to connect to, as well as uniquely identifying elements to
    ensure stable selection independent of other devices being connected.

    :return:
    """
    for port in slp.comports():
        print('''\
{port.device}
  name: {port.name}
  description: {port.description}
  hwid: {port.hwid}
  vid: {port.vid}
  pid: {port.pid}
  serial_number: {port.serial_number}
  location: {port.location}
  manufacturer: {port.manufacturer}
  product: {port.product}
  interface: {port.interface}
'''.format(port=port))


if __name__ == '__main__':
    show_port_details()
