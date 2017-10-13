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


wpos_x =   123.456
wpos_y =  -123.456
wpos_z =  7678.888

mpos_x =  8923.456
mpos_y = -8923.456
mpos_z =  8923.456

feed     = 14000
feed_ovr = 333

spindle     = 1020
spindle_ovr = 3020

step = 50

def packFloat(value) :
    data = [ 0x00 ] * 4
    valint = int(value)
    valflo = int((value - int(value)) * 10000.0)
    data[0] =  abs(valint) & 0xFF;
    data[1] = (abs(valint) >> 8) & 0xFF;
    data[2] =  abs(valflo) & 0xFF;
    data[3] = (abs(valflo) >> 8) & 0xFF;    
    
    if (valint < 0) :
        data[3] = data[3] | 0x80
    return data
          
def pack16(value) :
    return [ value & 0xFF, (value >> 8) & 0xFF ]


datain = [ 0x00 ] * 42

datain[ 0: 3]  = [ 0xFE, 0xFD, 0x0C ]

datain[ 3: 7] = packFloat(wpos_x)  # X
datain[ 7:11] = packFloat(wpos_y)  # Y
datain[11:15] = packFloat(wpos_z)  # Z

datain[15:19] = packFloat(mpos_x)  # X
datain[19:23] = packFloat(mpos_y)  # Y
datain[23:27] = packFloat(mpos_z)  # Z

datain[27:29] = pack16(feed)  
datain[29:31] = pack16(feed_ovr)  
datain[31:33] = pack16(spindle)  
datain[33:35] = pack16(spindle_ovr)  

if step == 0 :
    datain[35] = 0x00
if step == 1 :
    datain[35] = 0x01
if step == 5 :
    datain[35] = 0x02    
if step == 10 :
    datain[35] = 0x03
if step == 20 :
    datain[35] = 0x04
if step == 30 :
    datain[35] = 0x05
if step == 40 :
    datain[35] = 0x06    
if step == 50 :
    datain[35] = 0x07
if step == 100 :
    datain[35] = 0x08
if step == 500 :
    datain[35] = 0x09    
if step == 1000 :
    datain[35] = 0x0A
        
    
datain[36]     = 0x02


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
