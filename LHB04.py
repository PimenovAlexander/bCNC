#!/usr/bin/env python

import sys
import usb.core

from CNC import CNC


#
#   Button Mapping
# 
#
#     RESET=23       STOP=22
#     HOME=1         START/PAUSE=2         REWIND=3       PROBE-Z=4
#     SPINDLE=12     =1/2=6                =0=7           SAFE-Z=8
#     TOHOME=9       MACRO-1=10            MACRO-2=11     MACRO-3=5
#     STEP++=13      MPG=14                MACRO-6=15     MACRO-7=16




class LHB04Interface:
    
    def __init__(self):
        self.dev = None;
        self.endpoint = None;
       
       # Current state. update it and call updateOutput()
        self.wpos_x =   123.456
        self.wpos_y =  -123.456
        self.wpos_z =  7678.888

        self.mpos_x =  8923.456
        self.mpos_y = -8923.456
        self.mpos_z =  8923.456

        self.feed     = 14000
        self.feed_ovr = 333

        self.spindle     = 1020
        self.spindle_ovr = 3020

        self.step = 50
      
    def zero(self):
        self.wpos_x =  0
        self.wpos_y =  0
        self.wpos_z =  0

        self.mpos_x =  0
        self.mpos_y =  0
        self.mpos_z =  0

        self.feed     = 0
        self.feed_ovr = 0

        self.spindle     = 0
        self.spindle_ovr = 0

        self.step = 0
        
    def usbconnect(self):    
        self.dev = usb.core.find(idVendor=0x10ce, idProduct=0xeb70)
        if self.dev is None:
            print ("No CNC remote found in the system");
            return
            
        print("USB HB04 pendant found")
        print("Bus     :" + str(self.dev.bus))
        print("Address :" + str(self.dev.address))
        # print("Ports :" + str(self.dev.port_numbers))
        print("Port    :" + str(self.dev.port_number))
        

        try:
            if self.dev.is_kernel_driver_active(0) is True:
                self.dev.detach_kernel_driver(0)
        except usb.core.USBError as e:
            print ("Kernel driver won't give up control over device: %s" % str(e))
            print ("You can add udev rule:")
            print ("SUBSYSTEM==\"usb\", ATTR{idVendor}==\"0x10ce\", ATTR{idProduct}==\"0xeb70\", MODE=\"0666\"")
            print ("to /etc/udev/rules.d/99-lhb04.rules ")
            print ("udevadm control --reload-rules")
        try:
            self.dev.set_configuration()
            self.dev.reset()
        except usb.core.USBError as e:
            print ("Cannot set configuration the device: %s" % str(e))
            self.dev = None;
            return            

        self.endpoint = self.dev[0][(0,0)][0]

    # Packing data to pendant format
    def packFloat(self, value) :
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
            
    def pack16(self, value) :
        return [ value & 0xFF, (value >> 8) & 0xFF ]


    def updateOutput(self):    
        if self.dev is None :
            return;
        datain = [ 0x00 ] * 42
        datain[ 0: 3]  = [ 0xFE, 0xFD, 0x0C ]

        datain[ 3: 7] = self.packFloat(self.wpos_x)  # X
        datain[ 7:11] = self.packFloat(self.wpos_y)  # Y
        datain[11:15] = self.packFloat(self.wpos_z)  # Z

        datain[15:19] = self.packFloat(self.mpos_x)  # X
        datain[19:23] = self.packFloat(self.mpos_y)  # Y
        datain[23:27] = self.packFloat(self.mpos_z)  # Z

        datain[27:29] = self.pack16(self.feed)  
        datain[29:31] = self.pack16(self.spindle)  
        datain[31:33] = self.pack16(self.feed_ovr)  
        datain[33:35] = self.pack16(self.spindle_ovr)  

        if self.step == 0 :
            datain[35] = 0x00
        if self.step == 1 :
            datain[35] = 0x01
        if self.step == 5 :
            datain[35] = 0x02    
        if self.step == 10 :
            datain[35] = 0x03
        if self.step == 20 :
            datain[35] = 0x04
        if self.step == 30 :
            datain[35] = 0x05
        if self.step == 40 :
            datain[35] = 0x06    
        if self.step == 50 :
            datain[35] = 0x07
        if self.step == 100 :
            datain[35] = 0x08
        if self.step == 500 :
            datain[35] = 0x09    
        if self.step == 1000 :
            datain[35] = 0x0A
                
        datain[36]     = 0x02

        # print datain
        for pack in range(0, 6):
            out = self.dev.ctrl_transfer(0x21, 0x09, 0x0306, 0x00, [0x06] + datain[(pack * 7): (pack * 7 + 7)])
            # print out

    def pollPendant(self):
        if self.dev is None:
            return
        try:
            data = self.dev.read(self.endpoint.bEndpointAddress, self.endpoint.wMaxPacketSize, timeout=1)
            if data is not None and len(data) > 2:                
                return data
        except usb.core.USBError as e:
            if e.errno != 110: # 110 is a timeout.
                sys.exit("Error readin data: %s" % str(e))
        return None
    
    # ======== Related to CNC
    
    def updateCoords(self):
        self.wpos_x = CNC.vars["wx"];
        self.wpos_y = CNC.vars["wy"];
        self.wpos_z = CNC.vars["wz"];    
        
        self.mpos_x = CNC.vars["mx"];
        self.mpos_y = CNC.vars["my"];
        self.mpos_z = CNC.vars["mz"];    
                
        self.updateOutput();
    
##====================================================================================================    
    
    
def getClicks(value):    
    if value < 127:
        return value;
    return value - 256;
    

def mainLoop():
    print "Starting..."

    controller = LHB04Interface()
    controller.usbconnect();
    controller.updateOutput();

    controller.zero();
    controller.updateOutput();

    for i in range(0, 10) :
        controller.wpos_x += 1;
        controller.wpos_y += 3;
        controller.wpos_z += 7;    
        controller.updateOutput();

    controller.zero();
    controller.updateOutput();

    while 1:
        data = controller.pollPendant()    
        if data is None or len(data) <= 2:
            continue;
        
        print data
        
        # Buttons
        if data[1] == 13:
            if controller.step == 1:
                controller.step = 0;
            elif controller.step == 0:
                controller.step = 1; 
            
        
        if data[3] == 17:
            controller.wpos_x += controller.step * getClicks(data[4]);
        if data[3] == 18:
            controller.wpos_y += controller.step * getClicks(data[4]);
        if data[3] == 19:
            controller.wpos_z += controller.step * getClicks(data[4]);
            
        
        if data[3] == 21:
            controller.feed    += 10 * getClicks(data[4]);
            if controller.feed < 0 : controller.feed = 0;
            
        if data[3] == 20:
            controller.spindle += 100 * getClicks(data[4]);
            if controller.spindle < 0 : controller.spindle = 0;
        
        controller.updateOutput();
        
# mainLoop()

