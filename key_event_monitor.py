#!/usr/bin/python3
import keyboard
import threading

from key_detector import KeyDetector

class KeyEventMonitor(threading.Thread):
    def __init__(self, key_event_listener, key_exit_listener):
        threading.Thread.__init__(self)
        self.key_event_listener = key_event_listener
        self.key_exit_listener = key_exit_listener
        self.b_capture_keyboard = False
        self.key_detector = KeyDetector(
            self.handlePress, self.handleRelease, self.handleClick)

    def setCaptureKeyboard(self, bCaptureKeyboard):
        self.b_capture_keyboard = bCaptureKeyboard

    def handlePress(self, key_name):
        print(f'KeyEventMonitor.handlePress, key_name = {key_name}')
        self.key_event_listener(key_name, True)

    def handleRelease(self, key_name):
        print(f'KeyEventMonitor.handleRelease, key_name = {key_name}')
        self.key_event_listener(key_name, False)

    def handleClick(self, key_name):
        print(f'KeyEventMonitor.handleClick, key_name = {key_name}')
        self.key_event_listener(key_name, True)
        self.key_event_listener(key_name, False)

    def run(self):
        print('KeyEventMonitor thread start to run')
        while True:
            # Wait for the next event.
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN and event.name == 'esc':
                print('stop monitor key events')
                break

            if self.b_capture_keyboard:
                if event.event_type == keyboard.KEY_DOWN:
                    self.key_detector.onPressed(event.name)
                elif event.event_type == keyboard.KEY_UP:
                    self.key_detector.onReleased(event.name)

        if self.key_exit_listener != None:
            self.key_exit_listener()
        