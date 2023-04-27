#!/usr/bin/python3
import dbus.service
import bluetooth_constants
from gi.repository import GLib
from ble_base import Descriptor, Characteristic, Service
from key_event_name import *

REPORT_MAP = bytes((
    # Standard keyboard buttons
    0x05, 0x01,       # Usage Page (Generic Desktop)
    0x09, 0x07,       # Usage (Keyboard)
    0xA1, 0x01,       # Collection (Application)
    0x85, 0x01,  # Report ID (0x01)
    0x75, 0x01,  # Report Size (1)
    0x95, 0x08,  # Report Count (8)
    0x05, 0x07,  # Usage Page (Key Codes)
    0x19, 0xE0,  # Usage Minimum (224)
    0x29, 0xE7,  # Usage Maximum (231)
    0x15, 0x00,  # Logical Minimum (0)
    0x25, 0x01,  # Logical Maximum (1)
    0x81, 0x02,  # Input (Data, Variable, Absolute)
    0x81, 0x01,  # Input (Constant) – Reserved byte
    0x75, 0x01,  # Report Size (1)
    0x95, 0x05,  # Report Count (5)
    0x05, 0x08,  # Usage Page (LEDs)
    0x19, 0x01,  # Usage Minimum (1)
    0x29, 0x05,  # Usage Maximum (5)
    0x91, 0x02,  # Output (Data, Variable, Absolute)
    0x95, 0x03,  # Report Count (3)
    0x91, 0x01,  # Output (Constant)
    0x75, 0x08,  # Report Size (8)
    0x95, 0x06,  # Report Count (6)
    0x26, 0xFF, 0x00,  # Logical Maximum (255)
    0x05, 0x07,  # Usage Page (Key Codes)
    0x19, 0x00,  # Usage Minimum (0)
    0x2A, 0xFF, 0x00,  # Usage Maximum (255)
    0x81, 0x00,  # Input (Data, Array)
    0xC0,        # End Collection
    # Standard Consumer buttons
    0x05, 0x0C,       # Usage Page (Consumer Devices)
    0x09, 0x01,       # Usage (Consumer Control)
    0xA1, 0x01,       # Collection (Application)
    0x85, 0x0C,  # Report ID (0xOC)
    0x19, 0x00,  # Usage Minimum (0)
    0x2A, 0xFF, 0x03,  # Usage Maximum (0x03FF)
    0x75, 0x10,  # Report Size (16)
    0x95, 0x02,  # Report Count (2)
    0x15, 0x00,  # Logical Minimum (0)
    0x26, 0xFF, 0x03,  # Logical Maximum (0x03FF)
    0x81, 0x00,  # Input (Data, Array)
    0xC0,             # End collection
    # Standard AV control buttons
    0x05, 0x0C,       # Usage Page (Consumer Devices)
    0x09, 0x01,       # Usage (Consumer Control)
    0xA1, 0x01,       # Collection (Application)
    0x85, 0x10,  # Report ID (0x10)
    0x19, 0x00,  # Usage Minimum (0)
    0x2A, 0xFF, 0x03,  # Usage Maximum (0x03FF)
    0x75, 0x10,  # Report Size (16)
    0x95, 0x02,  # Report Count (2)
    0x15, 0x00,  # Logical Minimum (0)
    0x26, 0xFF, 0x03,  # Logical Maximum (0x03FF)
    0x81, 0x00,  # Input (Data, Array)
    0xC0,                # End collection
    0x06, 0xf0, 0xff, # Usage Page(0xFFF0, Vendor Specific 240)
    0xa1, 0x01,       # Collection(Application)
    0x85, 0xf4,       # Report ID(0xF4)
    0x06, 0xf0, 0xff, # Usage Page(0xFFF0, Vendor Specific)
    0x09, 0x03,       # Usage(0x03=Unpair from current remote)
    0x75, 0x08,       # Report Size(8)
    0x95, 0x01,       # Report Count(1)
    0x15, 0x00,       # Logical Minimum(0)
    0x26, 0xff, 0x00, # Logical Maximum(255)
    0x91, 0x02,       # Output(Data, Variable, Absolute)
    0x85, 0xf5,       # Report ID(0xF5)
    0x06, 0xF0, 0xff, # Usage Page(0xFFF0, Vendor Specific)
    0x09, 0x03,       # Usage(0x03=Unpair from current remote)
    0x75, 0x08,       # Report Size(8)
    0x95, 0x01,       # Report Count(1)
    0x15, 0x00,       # Logical Minimum(0)
    0x26, 0xff, 0x00, # Logical Maximum(255)
    0x81, 0x02,       # Input(Data, Variable, Absolute)
    0xc0, # End collection
))

g_service_registered_cb = None
class BatteryLevelCharacteristic(Characteristic):
    """
    Fake Battery Level characteristic. The battery level is drained by 2 points
    every 5 seconds.

    """
    BATTERY_LVL_UUID = '2a19'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.BATTERY_LVL_UUID,
                ['read', 'notify'],
                service)
        self.notifying = False
        self.notifyCnt = 0
        self.battery_lvl = 100

    def notify_battery_level(self):
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, {
                               'Value': [dbus.Byte(self.battery_lvl)]}, [])
        self.notifyCnt += 1
        
    def drain_battery(self):
        if not self.notifying: return True
        if(self.notifyCnt > 1): return False #Update battery level 2 times then stop
        
        if self.battery_lvl > 0:
            self.battery_lvl -= 2
            if self.battery_lvl < 5:
                #self.battery_lvl = 0
                GLib.source_remove(self.timer)
                
        #print('BatteryLevelCharacteristic, battery Level drained: ' + repr(self.battery_lvl))
        self.notify_battery_level()
        return True
 
    def ReadValue(self, options):
        print('Battery Level read: ' + repr(self.battery_lvl))
        return [dbus.Byte(self.battery_lvl)]

    def StartNotify(self):
        print('BatteryLevelCharacteristic.StartNotify')
        
        if self.notifying:
            print('BatteryLevelCharacteristic already notifying, nothing to do')
            return

        self.notifying = True
        self.timer = GLib.timeout_add(1000, self.drain_battery)

    def StopNotify(self):
        print('BatteryLevelCharacteristic StopNotify')

        if not self.notifying:
            print('BatteryLevelCharacteristic not notifying, nothing to do')
            return

        self.notifying = False


class BatteryService(Service):
    """
    Fake Battery service that emulates a draining battery.

    """
    PATH_BASE = bluetooth_constants.BLUEZ_OBJ_ROOT + "batt_service"
    SERVICE_UUID = '180f'

    def __init__(self, bus):
        Service.__init__(self, bus, self.PATH_BASE, self.SERVICE_UUID, True)
        self.add_characteristic(BatteryLevelCharacteristic(bus, 0, self))

"""
The Manufacturer Name String characteristic shall represent the name of the
manufacturer of the device.

Characteristic Behavior:
The Manufacturer Name String characteristic returns its value when read using the
GATT Characteristic Value Read procedure.
"""
class ManufacturerNameCharacteristic(Characteristic):
    CHARACTERISTIC_UUID = '2A29'
    MANUFACTURER_NAME = 'Fake RCU Manufacturer Name'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.CHARACTERISTIC_UUID,
                ["read"],
                service)
        self.value = dbus.Array(self.MANUFACTURER_NAME.encode(), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read RCU Manufacturer Name : {self.value}')
        return self.value

"""
The Model Number String characteristic shall represent the model number that is
assigned by the device vendor.

Characteristic Behavior:
The Model Number String characteristic returns its value when read using the GATT
Characteristic Value Read procedure.
"""
class ModelNumberCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A24'
    MODEL_NUMBER = 'FAKE_RCU_01'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.CHARACTERISTIC_UUID,
                ["read"],
                service)
        self.value = dbus.Array(self.MODEL_NUMBER.encode(), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read ModelNumberCharacteristic: {self.value}')
        return self.value

"""
The Software Revision String characteristic shall represent the software revision for the
software within the device.

Characteristic Behavior:
The Software Revision String characteristic returns its value when read using the GATT
Characteristic Value Read procedure.
"""
class VersionCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A28'
    VERSION_NUMBER = '1.0.0'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.CHARACTERISTIC_UUID,
                ["read"],
                service)
        
        self.value = dbus.Array(self.VERSION_NUMBER.encode(), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read VersionCharacteristic: {self.value}')
        return self.value

class DeviceInfoService(Service):

    SERVICE_UUID = '180A'
    PATH_BASE = bluetooth_constants.BLUEZ_OBJ_ROOT + "device_info_service"

    def __init__(self, bus):
        Service.__init__(self, bus, self.PATH_BASE, self.SERVICE_UUID, True)
        self.add_characteristic(ManufacturerNameCharacteristic(bus, 0, self))
        self.add_characteristic(ModelNumberCharacteristic(bus, 1, self))
        self.add_characteristic(VersionCharacteristic(bus, 2, self))

class ProtocolModeCharacteristic(Characteristic):
    CHARACTERISTIC_UUID = '2A4E'

    def __init__(self, bus, index, service):
        
        Characteristic.__init__(
                self, bus, index,
                self.CHARACTERISTIC_UUID,
                ["read", "write-without-response"],
                service)
        
        self.parent = service
        self.value = dbus.Array(bytearray.fromhex('01'), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read ProtocolMode ..')
        return self.value

    def WriteValue(self, value, options):
        print(f'Write ProtocolMode {value}')
        self.value = value


class HIDInfoCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A4A'
    HIDInfo = 'My HID'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.CHARACTERISTIC_UUID,
            ['read'],
            service)
        #self.value = dbus.Array(self.HIDInfo.encode(),
        #                        signature=dbus.Signature('y'))
        self.value = dbus.Array(bytearray.fromhex('01010002'), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read HIDInformation ..')
        return self.value

class ControlPointCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A4C'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.CHARACTERISTIC_UUID,
                ["write-without-response"],
                service)
        
        self.value = dbus.Array(bytearray.fromhex('00'), signature=dbus.Signature('y'))

    def WriteValue(self, value, options):
        print(f'Write ControlPoint {value}')
        self.value = value

class ReportMapCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A4B'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.CHARACTERISTIC_UUID,
                ['read'],
                service)
        '''
        <Field name="Report Map Value">
            <Requirement>Mandatory</Requirement>
            <Format>uint8</Format>
            <Repeated>true</Repeated>
        </Field>
        
        HID Report Descriptors https://www.usb.org/sites/default/files/documents/hid1_11.pdf
        HID Report Parser https://eleccelerator.com/usbdescreqparser/
        '''
        
        ##############################################################################################
        # This Report Descriptor defines 2 Input Reports
        # ReportMap designed by HeadHodge
        #
        # <Report Layouts>
        #   <Report>
        #       <ReportId>1</ReportId>
        #       <Description>HID Keyboard Input</Description>
        #       <Example>KeyCode capital 'M' = [dbus.Byte(0x02), dbus.Byte(0x10)]</Example>
        #       <Field>
        #           <Name>Keyboard Modifier</Name>
        #           <Size>uint8</Size>
        #           <Format>
        #               <Bit0>Left CTRL Key Pressed</Bit0>
        #               <Bit1>Left SHIFT Key Pressed</Bit1>
        #               <Bit2>Left ALT Key Pressed</Bit2>
        #               <Bit3>Left CMD(Window) Key Pressed</Bit3>
        #               <Bit4>Right CTRL Key Pressed</Bit4>
        #               <Bit5>Right SHIFT Key Pressed</Bit5>
        #               <Bit6>Right ALT Key Pressed</Bit6>
        #               <Bit7>Right CMD(Window) Key Pressed</Bit7>
        #           </Format>
        #       </Field>
        #       <Field>
        #           <Name>Keyboard Input KeyCode</Name>
        #           <Size>uint8</Size>
        #       </Field>
        #   </Report>
        #   <Report>
        #       <ReportId>2</ReportId>
        #       <Description>HID Consumer Input</Description>
        #       <Example>KeyCode 'VolumeUp' = [dbus.Byte(0xe9), dbus.Byte(0x00)]</Example>
        #       <Field>
        #           <Name>Consumer Input KeyCode</Name>
        #           <Size>uint16</Size>
        #       </Field>
        #   </Report>
        # </Report Layouts>
        ##############################################################################################
  
        #USB HID Report Descriptor
        self.value = dbus.Array(REPORT_MAP)

    def ReadValue(self, options):
        print(f'Read ReportMap ..')
        return self.value

class ComAVDescriptor(Descriptor):

    DESCRIPTOR_UUID = '2908'

    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
                self, bus, index,
                self.DESCRIPTOR_UUID,
                ['read'],
                characteristic)
                
        '''
        <Field name="Report ID">
            <Requirement>Mandatory</Requirement>
            <Format>uint8</Format>
            <Minimum>0</Minimum>
            <Maximum>255</Maximum>
        </Field>
        
        <Field name="Report Type">
            <Requirement>Mandatory</Requirement>
            <Format>uint8</Format>
            <Minimum>1</Minimum>
            <Maximum>3</Maximum>
            <Enumerations>
                <Enumeration value="Input Report" key="1"/>
                <Enumeration value="Output report" key="2"/>
                <Enumeration value="Feature Report" key="3"/>
                <ReservedForFutureUse start="4" end="255"/>
                <ReservedForFutureUse1 start1="0" end1="0"/>
            </Enumerations>
        </Field>
        '''
        # Thisuses ReportId 0x0c (Standard Consumer/AV control  buttons) defined in the ReportMap
        self.value = dbus.Array(bytearray.fromhex('0C01'), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read ComAVReportDescriptor ..')
        return self.value


class ConsumerCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A4D'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.CHARACTERISTIC_UUID,
            ['secure-read', 'notify'],
            service)

        '''
        <Field name="Report Value">
        <Requirement>Mandatory</Requirement>
        <Format>uint8</Format>
        <Repeated>true</Repeated>
        </Field>
        
        Use standard key codes: https://www.usb.org/sites/default/files/documents/hut1_12v2.pdf
        '''
        self.add_descriptor(ComAVDescriptor(bus, 1, self))

        self.value = [dbus.Byte(0x00), dbus.Byte(
            0x00), dbus.Byte(0x00), dbus.Byte(0x00)]

    def send(self, key_code_array):
        scan_code = [dbus.Byte(key_code) for key_code in key_code_array]
        print(
            f'ConsumerCharacteristic, send scan_code: {scan_code}')
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, {
                               'Value': scan_code}, [])
        print(f'ConsumerCharacteristic, sent')
        return True

    # This is not be read while service registered by central
    def ReadValue(self, options):
        print(f'Read ConsumerCharacteristic ..')
        return self.value

    # This is supposed not to be workable while central write value directly
    def WriteValue(self, value, options):
        print(f'Write ConsumerCharacteristic {value}')
        self.value = value

    def StartNotify(self):
        print(f'ConsumerCharacteristic.StartNotify() called')

    def StopNotify(self):
        print(f'ConsumerCharacteristic.StopNotify() called')


class STDKeyboardDescriptor(Descriptor):

    DESCRIPTOR_UUID = '2908'

    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
                self, bus, index,
                self.DESCRIPTOR_UUID,
                ['read'],
                characteristic)
                
        '''
        <Field name="Report ID">
            <Requirement>Mandatory</Requirement>
            <Format>uint8</Format>
            <Minimum>0</Minimum>
            <Maximum>255</Maximum>
        </Field>
        
        <Field name="Report Type">
            <Requirement>Mandatory</Requirement>
            <Format>uint8</Format>
            <Minimum>1</Minimum>
            <Maximum>3</Maximum>
            <Enumerations>
                <Enumeration value="Input Report" key="1"/>
                <Enumeration value="Output report" key="2"/>
                <Enumeration value="Feature Report" key="3"/>
                <ReservedForFutureUse start="4" end="255"/>
                <ReservedForFutureUse1 start1="0" end1="0"/>
            </Enumerations>
        </Field>
        '''
        # Thisuses ReportId 0x01(Standard keyboard buttons) as defined in the ReportMap characteristic
        self.value = dbus.Array(bytearray.fromhex('0101'), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Read STDKeyboardDescriptor ..')
        path = options['device']
        g_service_registered_cb(path)
        return self.value

class STDKeyboardCharacteristic(Characteristic):

    CHARACTERISTIC_UUID = '2A4D'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.CHARACTERISTIC_UUID,
                ['secure-read', 'notify'],
                service)
                
        '''
        <Field name="Report Value">
        <Requirement>Mandatory</Requirement>
        <Format>uint8</Format>
        <Repeated>true</Repeated>
        </Field>
        
        Use standard key codes: https://www.usb.org/sites/default/files/documents/hut1_12v2.pdf
        '''
        self.add_descriptor(STDKeyboardDescriptor(bus, 1, self))
        
        self.value = [dbus.Byte(0x00), dbus.Byte(0x00), dbus.Byte(0x00), dbus.Byte(0x00), 
                      dbus.Byte(0x00), dbus.Byte(0x00), dbus.Byte(0x00), dbus.Byte(0x00)]
        
    def send(self, key_code_array):
        scan_code_press = [dbus.Byte(key_code) for key_code in key_code_array]
        scan_code_release = [dbus.Byte(0x00) for i in key_code_array]
        print(
            f'STDKeyboardCharacteristic, send scan_code_press: {scan_code_press}')
        print(
            f'STDKeyboardCharacteristic, send scan_code_release: {scan_code_release}')
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, {
                               'Value': scan_code_press}, [])
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, {
                               'Value': scan_code_release}, [])
        print(f'STDKeyboardCharacteristic, sent')
        return True

    def ReadValue(self, options):
        print(f'Read STDKeyboardCharacteristic ..')
        return self.value

    # This is supposed not to be workable while central write value directly
    def WriteValue(self, value, options):
        print(f'Write STDKeyboardCharacteristic {value}')
        self.value = value

    def StartNotify(self):
        print(f'STDKeyboardCharacteristic.StartNotify() called')

    def StopNotify(self):
        print(f'STDKeyboardCharacteristic.StopNotify() called')


KEY_CODE = "key_code"
KEY_REPORT_ID = "key_report_id"
KEY_REPORT_ID_CONSUMER = 0x0C
KEY_REPORT_ID_STANDARD_KEYBOARD = 0x01
KEK_MAP = {
    # key left
    KEY_EVENT_NAME_LEFT: {KEY_CODE: [0x44, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key right
    KEY_EVENT_NAME_RIGHT: {KEY_CODE: [0x45, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key up
    KEY_EVENT_NAME_UP: {KEY_CODE: [0x42, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key down
    KEY_EVENT_NAME_DOWN: {KEY_CODE: [0x43, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key select
    KEY_EVENT_NAME_SEL: {KEY_CODE: [0x41, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key volume up
    KEY_EVENT_NAME_VOLUP: {KEY_CODE: [0xe9, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key volume down
    KEY_EVENT_NAME_VOLDW: {KEY_CODE: [0xea, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key tivo
    KEY_EVENT_NAME_TIVO: {KEY_CODE: [0x3d, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key voice
    KEY_EVENT_NAME_VOICE: {KEY_CODE: [0x21, 0x02, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key apps
    KEY_EVENT_NAME_APPS: {KEY_CODE: [0x3e, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key mute
    KEY_EVENT_NAME_MUTE: {KEY_CODE: [0xe2, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key power
    KEY_EVENT_NAME_POWER: {KEY_CODE: [0x30, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key back
    KEY_EVENT_NAME_BACK: {KEY_CODE: [0x24, 0x02, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key release
    KEY_EVENT_NAME_RELEASE : {KEY_CODE: [0x00, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},
    # key 0
    KEY_EVENT_NAME_0: {KEY_CODE: [0x00, 0x00, 0x27, 0x00, 0x00, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_STANDARD_KEYBOARD},
    # key 1
    KEY_EVENT_NAME_1: {KEY_CODE: [0x00, 0x00, 0x1e, 0x00, 0x00, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_STANDARD_KEYBOARD},
    # key 2
    KEY_EVENT_NAME_2: {KEY_CODE: [0x00, 0x00, 0x1f, 0x00, 0x00, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_STANDARD_KEYBOARD},
    # key 3
    KEY_EVENT_NAME_3: {KEY_CODE: [0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_STANDARD_KEYBOARD},
    # key 4
    KEY_EVENT_NAME_4: {KEY_CODE: [0x00, 0x00, 0x21, 0x00, 0x00, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_STANDARD_KEYBOARD},
    # key 5
    KEY_EVENT_NAME_5: {KEY_CODE: [0x00, 0x00, 0x22, 0x00, 0x00, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_STANDARD_KEYBOARD},
    # key 6
    KEY_EVENT_NAME_6: {KEY_CODE: [0x00, 0x00, 0x23, 0x00, 0x00, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_STANDARD_KEYBOARD},
    # key 7
    KEY_EVENT_NAME_7: {KEY_CODE: [0x00, 0x00, 0x24, 0x00, 0x00, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_STANDARD_KEYBOARD},
    # key 8
    KEY_EVENT_NAME_8: {KEY_CODE: [0x00, 0x00, 0x25, 0x00, 0x00, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_STANDARD_KEYBOARD},
    # key 9
    KEY_EVENT_NAME_9: {KEY_CODE: [0x00, 0x00, 0x26, 0x00, 0x00, 0x00, 0x00, 0x00], KEY_REPORT_ID: KEY_REPORT_ID_STANDARD_KEYBOARD},
}


class HIDService(Service):
    SERVICE_UUID = '1812'
    PATH_BASE = bluetooth_constants.BLUEZ_OBJ_ROOT + "hid_service"

    class KeyEvent:
        def __init__(self, key_code, key_category):
            self.key_code = key_code
            self.key_category = key_category

    def __init__(self, bus, service_registered_cb):
        Service.__init__(self, bus, self.PATH_BASE, self.SERVICE_UUID, True)

        self.protocolMode = ProtocolModeCharacteristic(bus, 0, self)
        self.hidInfo = HIDInfoCharacteristic(bus, 1, self)
        self.controlPoint = ControlPointCharacteristic(bus, 2, self)
        self.reportMap = ReportMapCharacteristic(bus, 3, self)
        self.reportConsumer = ConsumerCharacteristic(bus, 4, self)
        self.reportSTDKeyboard = STDKeyboardCharacteristic(bus, 5, self)

        global g_service_registered_cb
        g_service_registered_cb = service_registered_cb

        self.add_characteristic(self.protocolMode)
        self.add_characteristic(self.hidInfo)
        self.add_characteristic(self.controlPoint)
        self.add_characteristic(self.reportMap)
        self.add_characteristic(self.reportConsumer)
        self.add_characteristic(self.reportSTDKeyboard)

    def onKeyEvent(self, key_event_name):
        key_info = KEK_MAP.get(key_event_name)
        #print(f'key_info:{key_info}')
        if key_info != None:
            if key_info[KEY_REPORT_ID] == KEY_REPORT_ID_CONSUMER:
                self.reportConsumer.send(key_info[KEY_CODE])
            elif key_info[KEY_REPORT_ID] == KEY_REPORT_ID_STANDARD_KEYBOARD:
                self.reportSTDKeyboard.send(key_info[KEY_CODE])
