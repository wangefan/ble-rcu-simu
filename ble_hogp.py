#!/usr/bin/python3
import dbus.service
import bluetooth_constants
from gi.repository import GLib
from ble_base import Descriptor, Characteristic, Service

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
        #self.timer = GObject.timeout_add(60000, self.drain_battery)

    def notify_battery_level(self):
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, { 'Value': [dbus.Byte(self.battery_lvl)] }, [])
        self.notifyCnt += 1
        
    def drain_battery(self):
        if not self.notifying: return True
        if(self.notifyCnt > 2): return False #Update battery level 3 times then stop
        
        if self.battery_lvl > 0:
            self.battery_lvl -= 2
            if self.battery_lvl < 5:
                #self.battery_lvl = 0
                GLib.source_remove(self.timer)
                
        print('Battery Level drained: ' + repr(self.battery_lvl))
        self.notify_battery_level()
        return True
 
    def ReadValue(self, options):
        print('Battery Level read: ' + repr(self.battery_lvl))
        return [dbus.Byte(self.battery_lvl)]

    def StartNotify(self):
        print('Start Battery Notify')
        
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True
        print('Battery Notify 1')
        self.timer = GLib.timeout_add(2000, self.drain_battery)

    def StopNotify(self):
        print('Stop Battery Notify')
        
        if not self.notifying:
            print('Not notifying, nothing to do')
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
        print(f'Read ProtocolMode: {self.value}')
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
        print(f'HIDInfoCharacteristic, Read HIDInformation: {self.value}')
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
        print(f'ReportMapCharacteristic, Read ReportMap: {self.value}')
        return self.value

class Report1ReferenceDescriptor(Descriptor):

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
        # This report uses ReportId 0x0c as defined in the ReportMap characteristic
        self.value = dbus.Array(bytearray.fromhex('0C01'), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Report1ReferenceDescriptor, Read ReportReference: {self.value}')
        return self.value

class ReportConsumerCharacteristic(Characteristic):

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
        self.add_descriptor(Report1ReferenceDescriptor(bus, 1, self))
        
        self.value = [dbus.Byte(0x00), dbus.Byte(
            0x00), dbus.Byte(0x00), dbus.Byte(0x00)]
        
        
    def send(self, key_code):
        print(f'ReportConsumerCharacteristic, send keyCode: {key_code}')
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, {
                               'Value': [dbus.Byte(key_code), dbus.Byte(0x00), dbus.Byte(0x00), dbus.Byte(0x00)]}, [])
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, {
                               'Value': [dbus.Byte(0x00), dbus.Byte(0x00), dbus.Byte(0x00), dbus.Byte(0x00)]}, [])
        print(f'ReportConsumerCharacteristic, sent')
        return True
                
    def ReadValue(self, options):
        print(f'ReportConsumerCharacteristic, Read Report: {self.value}')
        return self.value

    def WriteValue(self, value, options):
        print(f'ReportConsumerCharacteristic, Write Report {self.value}')
        self.value = value

    def StartNotify(self):
        print(f'ReportConsumerCharacteristic.StartNotify() called')

    def StopNotify(self):
        print(f'ReportConsumerCharacteristic.StopNotify() called')

class Report2ReferenceDescriptor(Descriptor):

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
        # This report uses ReportId 0x10 as defined in the ReportMap characteristic
        self.value = dbus.Array(bytearray.fromhex('1001'), signature=dbus.Signature('y'))

    def ReadValue(self, options):
        print(f'Report2ReferenceDescriptor, Read ReportReference: {self.value}')
        return self.value

class Report2Characteristic(Characteristic):

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
        self.add_descriptor(Report2ReferenceDescriptor(bus, 1, self))
        
        self.value = [dbus.Byte(0x00), dbus.Byte(
            0x00), dbus.Byte(0x00), dbus.Byte(0x00)]
        
    def send(self):
        #send keyCode: 'VolumeUp'
        print(f'Report2Characteristic, send keyCode: "VolumeUp"***')
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, {
                               'Value': [dbus.Byte(0xE9), dbus.Byte(0x00), dbus.Byte(0x00), dbus.Byte(0x00)]}, [])
        self.PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, {
                               'Value': [dbus.Byte(0x00), dbus.Byte(0x00), dbus.Byte(0x00), dbus.Byte(0x00)]}, [])
        print(f'Report2Characteristic, sent')
        return True
                
    def ReadValue(self, options):
        print(f'Report2Characteristic, Read Report: {self.value}')
        return self.value

    def WriteValue(self, value, options):
        print(f'Report2Characteristic, Write Report {self.value}')
        self.value = value

    def StartNotify(self):
        print(f'Report2Characteristic, Start Report Consumer Input')
        self.timer = GLib.timeout_add(15000, self.send)
        print(f'Report2Characteristic, Start Report Consumer Input end')

    def StopNotify(self):
        print(f'Report2Characteristic, Stop Start Report Consumer Input')


KEY_CODE = "key_code"
KEY_REPORT_ID = "key_report_id"
KEY_REPORT_ID_CONSUMER = 0x0C
KEK_MAP = {
    'left': {KEY_CODE: 0x44, KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},  # key left
    'right': {KEY_CODE: 0x45, KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER}, # key right
    'up': {KEY_CODE: 0x42, KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},    # key up
    'down': {KEY_CODE: 0x43, KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},  # key down
    'help': {KEY_CODE: 0xe9, KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},  # key volume up
    'f14': {KEY_CODE: 0xea, KEY_REPORT_ID: KEY_REPORT_ID_CONSUMER},   # key volume down
}


class HIDService(Service):
    SERVICE_UUID = '1812'
    PATH_BASE = bluetooth_constants.BLUEZ_OBJ_ROOT + "hid_service"

    class KeyEvent:
        def __init__(self, key_code, key_category):
            self.key_code = key_code
            self.key_category = key_category

    def __init__(self, bus):
        Service.__init__(self, bus, self.PATH_BASE, self.SERVICE_UUID, True)

        self.protocolMode = ProtocolModeCharacteristic(bus, 0, self)
        self.hidInfo = HIDInfoCharacteristic(bus, 1, self)
        self.controlPoint = ControlPointCharacteristic(bus, 2, self)
        self.reportMap = ReportMapCharacteristic(bus, 3, self)
        self.reportConsumer = ReportConsumerCharacteristic(bus, 4, self)
        # self.report2 = Report2Characteristic(bus, 5, self)

        self.add_characteristic(self.protocolMode)
        self.add_characteristic(self.hidInfo)
        self.add_characteristic(self.controlPoint)
        self.add_characteristic(self.reportMap)
        self.add_characteristic(self.reportConsumer)
        # self.add_characteristic(self.report2)

    def onKeyEvent(self, key_event):
        key_info = KEK_MAP.get(key_event.name)
        print(f'key_info:{key_info}')
        if key_info != None:
            if key_info[KEY_REPORT_ID] == KEY_REPORT_ID_CONSUMER:
                self.reportConsumer.send(key_info[KEY_CODE])
