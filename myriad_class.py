from os import terminal_size
import usb.core
import sys

delchars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())


class MyriadAmpConnection(object):

    def __init__(self):

        VENDOR_ID = 0x0483
        PRODUCT_ID = 0x5740
        self.dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

        if self.dev is None:
            raise ValueError('not connected')
            sys.exit(1)

        i = self.dev[0].interfaces()[1].bInterfaceNumber

        if self.dev.is_kernel_driver_active(i):
            try:
                self.dev.detach_kernel_driver(i)
            except usb.core.USBError as e:
                sys.exit(
                    "Could not detatch kernel driver from interface({0}): {1}".format(i, str(e)))

        self.offset_steps = 1
        self.new_volume_offset = 0
        self.myriad_settings = {}
        self.get_current_myriad_settings()

    def send_command(self, command):
        try:
            self.dev.read(0x81, 64, 1)
        except:
            pass
        msg = 'cmd -' + command + '\r'
        try:
            self.dev.write(1, msg, 1000)
            result = ''.join([chr(x) for x in self.dev.read(0x81, 64, 1000)]).replace(
                "\n", "").replace("  ", " ")
        except usb.core.USBTimeoutError:
            result = ''
        return result

    def send_query(self, query):
        try:
            self.dev.read(0x81, 64, 1)
        except:
            pass
            # print("Myriad amplifier write buffer clear.")
        #print("Sending " + command)
        self.dev.write(1, 'cmd -Q00' + '\r', 1000)
        result = ''.join([chr(x) for x in self.dev.read(0x81, 64, 1000)]).replace(
            "\n", "").replace("  ", " ")
        return result

    def to_alphanum(self, text): 
        return ''.join([char for char in text if char.isalnum()]) 

    def get_current_ambientDB(self):

        c = []
        b = self.send_command("0")
        if len(b) > 0:
            if b[0] == "V":
                c = b.split(' ')
                if len(c) >= 4:
                    if len(c[2]) == 2:
                        dB = c[2]
                    else:
                        dB = 0
                else:
                    dB = 0
            else:
                dB = 0
        else:
            dB = 0
        self.myriad_settings.update({'current_ambient_db': dB})
        return self.myriad_settings

    def get_current_myriad_settings(self):

        #print(f"Fetching current Myriad settings")
        b = self.send_command("1")
        #print(b)
        # print(b)
        if len(b) > 0:
            if b[0] == "V":
                c = b.split(' ')
                if len(c) >= 5:
                    self.myriad_settings.update({'vol_offset': str(c[5])})
        return self.myriad_settings

    def update_myriad_volume_offset(self, increment):

        temp_increment = int(increment)
        self.new_volume_offset = int(self.myriad_settings.get('vol_offset')) + (self.offset_steps * temp_increment)
        
        if self.send_command("L0300" + str(hex(self.new_volume_offset)).upper()[-2:]) == 'OK':
            self.myriad_settings.update({'vol_offset': str(self.new_volume_offset)})
            print('yay')

        return self.myriad_settings

    def destroy(self):

        usb.util.dispose_resources(self.dev)
