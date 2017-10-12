#!/usr/bin/env python

import sys, usb.core

dev = usb.core.find(idVendor=0x10ce, idProduct=0xeb70)
if dev is None:
    sys.exit("No CNC remote found in the system");

try:
    if dev.is_kernel_driver_active(0) is True:
        dev.detach_kernel_driver(0)
except usb.core.USBError as e:
    sys.exit("Kernel driver won't give up control over device: %s" % str(e))

try:
    dev.set_configuration()
    dev.reset()
except usb.core.USBError as e:
    sys.exit("Cannot set configuration the device: %s" % str(e))

endpoint = dev[0][(0,0)][0]

datain = [ 0x00 ] * 42
datain[ 0:3]  = [ 0xFE, 0xFD, 0x0C ]
datain[ 3:7]  = [ 0x10, 0x10, 0x00, 0x00 ]  # X
datain[ 7:11] = [ 0x00, 0x00, 0x00, 0x00 ]  # Y
datain[11:15] = [ 0x00, 0x00, 0x00, 0x00 ]  # Z

#datain = datain + [ 0x00, 0x00 ]  # feed
#datain = datain + [ 0x00, 0x00 ]  # spindle
#datain = datain + [ 0x00, 0x00 ]  # feed
#datain = datain + [ 0x00, 0x00 ]  # spindle

print datain
for pack in range(0, 6):
    out = dev.ctrl_transfer(0x21, 0x09, 0x0306, 0x00, [0x06] + datain[(pack * 7): (pack * 7 + 7)])
    print out

quit()


#dev.ctrl_transfer(0x40, CTRL_LOOPBACK_WRITE, 0, 0, msg) == len(msg)
#ret = dev.ctrl_transfer(0xC0, CTRL_LOOPBACK_READ, 0, 0, len(msg))



while 1:
    try:
        data = dev.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize, timeout=10000)
        if data is not None and len(data) > 2:
            print data
    except usb.core.USBError as e:
        if e.errno != 110: # 110 is a timeout.
            sys.exit("Error readin data: %s" % str(e))
