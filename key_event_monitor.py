#!/usr/bin/python3
import keyboard
import threading

class KeyEventMonitor(threading.Thread):
    def __init__(self, key_event_listener, key_exit_listener):
        threading.Thread.__init__(self)
        self.key_event_listener = key_event_listener
        self.key_exit_listener = key_exit_listener

    def run(self):
        print('KeyEventMonitor thread start to run')
        while True:
            # Wait for the next event.
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_UP:
                if event.name == 'q':
                    print('stop monitor key events')
                    break
                else:
                    if self.key_event_listener != None:
                        self.key_event_listener(event)

        if self.key_exit_listener != None:
                        self.key_exit_listener()
        