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
        print(f"Agent.set_trusted, device = {device}")
        props = dbus.Interface(self.bus.get_object(
            bluetooth_constants.BLUEZ_SERVICE_NAME, device), bluetooth_constants.DBUS_PROPERTIES)
        props.Set("org.bluez.Device1", "Trusted", True)
        print("Agent.set_trusted ok")

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="", out_signature="")
    def Release(self):
        print("Agent.Release")
        if self.exit_on_release:
            mainloop.quit()

    # This method gets called when the service daemon
    # needs to authorize a connection/service request.
    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print("Agent.AuthorizeService (%s, %s), always authorize services!" %
              (device, uuid))
        return

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        print("Agent.RequestPinCode (%s)" % (device))
        self.set_trusted(device)
        return ask("Enter PIN Code: ")

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        print("Agent.RequestPasskey (%s)" % (device))
        self.set_trusted(device)
        passkey = ask("Enter passkey: ")
        return dbus.UInt32(passkey)

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        print("Agent.DisplayPasskey (%s, %06u entered %u)" %
              (device, passkey, entered))

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        print("Agent.DisplayPinCode (%s, %s)" % (device, pincode))

    # This method gets called when the service daemon
    # needs to confirm a passkey for an authentication.
    # To confirm the value it should return an empty reply
    # or an error in case the passkey is invalid.
    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print("Agent.RequestConfirmation (%s, %06d), always confirm!" %
              (device, passkey))
        self.set_trusted(device)
        return

    # This method gets called to request the user to
    # authorize an incoming pairing attempt which
    # would in other circumstances trigger the just-works
    # model.
    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        print("Agent.RequestAuthorization (%s), always authorize!" % (device))
        return

    @dbus.service.method(bluetooth_constants.AGENT_INTERFACE,
                         in_signature="", out_signature="")
    def Cancel(self):
        print("Agent.Cancel get called")
