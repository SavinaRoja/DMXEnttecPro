# DMXEnttecPro
Control the Enttec DMX USB Pro with Python3

## Installation

This package solely depends on `pyserial`. You can install a recent release on
PyPI:

`pip install DMXEnttecPro`

or by getting the [repository from GitHub](https://github.com/SavinaRoja/DMXEnttecPro)
and doing something along the lines of:
```
git clone git@github.com:SavinaRoja/DMXEnttecPro.git
cd DMXEnttecPro
pip install .
```

## Getting Started

If you don't know the serial address of the DMX controller yet, you can do the
following to identify it:

`python -m DMXEnttecPro.utils`

which will give you some detailed information on all COM ports like this:

```
COM4
  name: None
  description: USB Serial Port (COM4)
  hwid: USB VID:PID=0403:6001 SER=EN055555A
  vid: 1027
  pid: 24577
  serial_number: EN055555A
  location: None
  manufacturer: FTDI
  product: None
  interface: None
```

Once you know your serial address, setting up a connection to your Enttec DMX
USB Pro is simple:

```
from DMXEnttecPro import Controller
#dmx = Controller('COM4')  # Typical of Windows
dmx = Controller('/dev/ttyUSB0')  # Typical of Linux
```

Then you can set channel values easily (DMX Channels are 1-indexed, and
`Controller` maintains that convention for you.) with:

```
dmx.set_channel(1, 255)  # Sets DMX channel 1 to max 255
dmx.submit()  # Sends the update to the controller
```

In some environments where you may not be assured of the precise string of your
COM port, I recommend using a uniquely identifying mark like the serial number
or product ID. Some helpers exist in `DMXEnttecPro.utils`:

```
from DMXEnttecPro import Controller
from DMXEnttecPro.utils import get_port_by_serial_number, get_port_by_product_id
my_port = get_port_by_serial_number('EN055555A')
my_port = get_port_by_product_id(24577)
dmx = Controller(my_port)
```

## Additional Features

There are three main additional features that this package offers:
auto-submission of changes, configurable size of DMX universe, and dynamic
submission.

### Auto-submission

You may supply `auto_submit=True` to instantiation of `Controller` to tell it
to automatically submit changes on any action changing channel values:

```
dmx = Controller('/dev/ttyUSB0', auto_submit=True)
```

The argument `submit_after=<bool>` can be provided to any action changing
channel values and it will take precedence over the configured `auto_submit`
value of the `Controller`.

### DMX Size Configuration

The size of the DMX universe defaults to 512 channels. There are apparently
occasions where finer timescales can be achieved in DMX by constraining this.
`dmx_size=<int>` may be supplied to instantiation of `Controller`.

```
dmx = Controller('/dev/ttyUSB0', dmx_size=256)  # use only 256 channels
```

### Dynamic Submission

The `Controller` can determine the fewest number of channels it must send to the
DMX controller to update and possibly give finer timescales. Supply
`dynamic_submission=True` to instantiation of `Controller` to enable this.

```
dmx = Controller('/dev/ttyUSB0', dynamic_submission=True)
```

If it determines that there are no channels to update, it will omit sending any
message to the DMX controller.

## Acknowledgments

DMXEnttecPro evolved from my re-write of [pysimpledmx](https://github.com/c0z3n/pySimpleDMX)
for compatibility with Python3.

[pyenttec](https://github.com/generalelectrix/pyenttec) is another good package
that seems to have also implemented some configuration of the Enttec DMX USB
Pro that I have not (at present) implemented.

## Developing

So far I have only utilized features with which I am personally familiar and
have wanted. Please submit any issues or feature requests along with usage
needs and I would be happy to evaluate them.
