# coding: utf-8

import serial.tools.list_ports as slp


# Important docs: https://pyserial.readthedocs.io/en/latest/tools.html
def get_port_by_serial_number(serial_number: str):
    all_ports = slp.comports()
    for port in all_ports:
        if port.serial_number == serial_number:
            return port.device
    # No port could be found for the serial number
    raise ValueError('No COM device found with serial {}'.format(serial_number))


def get_port_by_product_id(product_id: int):
    all_ports = slp.comports()
    for port in all_ports:
        if port.pid == product_id:
            return port.device
    # No port could be found for the serial number
    raise ValueError('No COM device found with product id {}'.format(product_id))


def show_port_details():
    for port in slp.comports():
        print(f'''\
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
''')

if __name__ == '__main__':
    show_port_details()
