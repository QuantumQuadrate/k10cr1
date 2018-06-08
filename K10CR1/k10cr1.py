import serial
import math
from serial.tools import list_ports


class K10CR1:
    """Thorlabs K10CR1 rotation stage class."""

    def __init__(self,  ser_num):
        """Set up and connect to device with serial number: ser_num"""
        self.ser_num = ser_num
        self.ready = False
        self.connect()
        if not self.ready:
            print('Unable to connect to device with serial number: {}'.format(ser_num))
        else:
            print('Connect successful to device with serial number: {}'.format(ser_num))

    def connect(self):
        """Searches all com ports for device with matching serial number
        and opens a connection
        """
        ports = list_ports.comports()
        for port in ports:
            print(port)
            # condition from from Xiayuo's old code, not sure if length check is necessary
            # VID:PID=0403:faf0
            # DWB: length check is not necessary...
            if (port[2][26:].startswith(self.ser_num):
                self.ser = serial.Serial(baudrate=115200, timeout=0.1, port=port[0])
                self.ready = True
                break

    def angle_to_DU(self, ang):
        return int(ang*24576000/180)

    def DU_to_angle(self, DU):
        return (DU*180/24576000)

    def dth(self, x, bytelen):
        # print(x, '---', bytelen)
        if x >= 0:
            hstring = hex(x)
            hstring = hstring[2:]
            while(len(hstring) < 2*bytelen):
                hstring = '0'+hstring
            count = 0
            new = list(hstring)
            while count < bytelen*2:
                tmp = new[count]
                new[count] = new[count+1]
                new[count+1] = tmp
                count = count+2
            hstring = ''.join(new)
            hstring = hstring[::-1]
            return hstring
        elif x < 0:
            y = abs(x)
            bstring = bin(y)
            bstring = bstring[2:]
            while(len(bstring) < 2*bytelen*4):
                bstring = '0'+bstring
            # print(bstring)
            count = 0
            new = list(bstring)
            while count < 2*bytelen*4:
                if new[count] == '1':
                    new[count] = '0'
                else:
                    new[count] = '1'
                count = count+1

            bstring = ''.join(new)
            # print(bstring)
            count = 2*bytelen*4-1
            add = '1'
            while count > -1:
                if new[count] != add:
                    add = '0'
                    new[count] = '1'
                else:
                    new[count] = '0'
                count = count-1
            bstring = ''.join(new)
            # print(bstring)
            hstring = hex(int(bstring, 2))
            hstring = hstring[2:]
            while(len(hstring) < 2*bytelen):
                hstring = '0'+hstring
            count = 0
            new = list(hstring)
            while count < bytelen*2:
                tmp = new[count]
                new[count] = new[count+1]
                new[count+1] = tmp
                count = count+2
            hstring = ''.join(new)
            hstring = hstring[::-1]
            lenhstring = len(hstring)
            if lenhstring > 2*bytelen:
                hstring = hstring[1:]
            # print(hstring)
            return hstring

    def btd(self, x):
        bytelen = len(x)
        count = 0
        dvalue = 0
        while(count < bytelen):
            dvalue = dvalue+x[count]*(math.pow(256, count))
            count = count+1
        bstring = bin(int(dvalue))
        if len(bstring) < 2*bytelen*4+2:
            return int(dvalue)
        elif len(bstring) > 2*bytelen*4+2:
            print('Error:Error in byte conversion')
        else:
            bstring = bin(int(dvalue-1))
            bstring = bstring[2:]
            count = 0
            new = list(bstring)
            while count < 2*bytelen*4:
                if new[count] == '1':
                    new[count] = '0'
                else:
                    new[count] = '1'
                count = count+1
            bstring = ''.join(new)
            return (int(bstring, 2))*(-1)

    def htb(self, x):
        # print(x)
        return bytearray.fromhex(x)

    def rd(self, bytelen):
        x = self.ser.readline()
        while(len(x) < bytelen):
            x = x+self.ser.readline()
        return x

    def write(self, x):
        command = self.htb(x)
        # print(command)
        return self.ser.write(command)

    def identify(self):
        return self.write('230200005001')

    def home(self):
        self.write('430401005001')
        return self.rd(6)

    def moverel(self, x):
        relpos = self.dth(self.angle_to_DU(x), 4)
        chan = '0100'
        header = '48040600d001'
        hcmd = header+chan+relpos
        # print(hcmd)
        self.write(hcmd)
        # return self.rd(20)

    def moveabs(self, x):
        abspos = self.dth(self.angle_to_DU(x), 4)
        chan = '0100'
        header = '53040600d001'
        hcmd = header+chan+abspos
        # print(hcmd)
        self.write(hcmd)
        # return rd(20)

    def jog(self):
        self.write('6a0401015001')
        return self.rd(20)

    def getpos(self):
        self.write('110401005001')
        bytedata = self.rd(12)
        bytedata = bytedata[8:]
        x = self.DU_to_angle(self.btd(bytedata))
        return float('%.3f' % x)
