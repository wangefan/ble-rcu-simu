#!/usr/bin/python3
import dbus.service
import bluetooth_constants


def ask(prompt):
    try:
        return raw_input(prompt)
    except:
        return input(prompt)

class Agent(dbus.service.Object):

    def __init__(self, bus, path):
        self.bus = bus
        self.exit_on_release = False
        dbus.service.Object.__init__(self, bus, path)

    def set_exit_on_release(self, exit_on_release):
        self.exit_on_release = exit_on_release

    def set_trusted(self, device):
        print(f"set_trusted, device = {device}")
        props = dbus.Interface(self.bus.get_object(
            bluetooth_constants.BLUEZ_SERVICE_NAME, device), bluetooth_constants.DBUS_PROPERTIES)
        props.Set("org.bluez.Device1", "Trusted", True)
        print("set_trusted ok")

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="", out_signature="")
    def Release(self):
        print("Release")
        if self.exit_on_release:
            mainloop.quit()

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print("AuthorizeService (%s, %s)" % (device, uuid))
        #authorize = ask("Authorize connection (yes/no): ")
        #if (authorize == "yes"):
        return
        #raise bluetooth_exceptions.Rejected("Connection rejected by user")

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        print("RequestPinCode (%s)" % (device))
        self.set_trusted(device)
        return ask("Enter PIN Code: ")

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        print("RequestPasskey (%s)" % (device))
        self.set_trusted(device)
        passkey = ask("Enter passkey: ")
        return dbus.UInt32(passkey)

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        print("DisplayPasskey (%s, %06u entered %u)" %
              (device, passkey, entered))

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        print("DisplayPinCode (%s, %s)" % (device, pincode))

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print("RequestConfirmation (%s, %06d)" % (device, passkey))
        #confirm = ask("Confirm passkey (yes/no): ")
        #if (confirm == "yes"):
        self.set_trusted(device)
        return
        #raise bluetooth_exceptions.Rejected("Passkey doesn't match")

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        print("RequestAuthorization (%s)" % (device))
        #auth = ask("Authorize? (yes/no): ")
        #if (auth == "yes"):
        return
        #raise bluetooth_exceptions.Rejected("Pairing rejected")

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="", out_signature="")
    def Cancel(self):
        print("Cancel")
