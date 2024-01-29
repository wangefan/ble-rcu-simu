#!/usr/bin/python3
import threading

from key_detector import KeyDetector

import os
import pickle
from gesture_event import GestureEvent

PIPE_PATH = "/GestureEventPipe"

class GestureMonitor(threading.Thread):
    def __init__(self, key_event_listener):
        threading.Thread.__init__(self)
        self.key_event_listener = key_event_listener
        self.key_detector = KeyDetector(
            self.handlePress, self.handleRelease, self.handleClick
        )
        if os.path.exists(PIPE_PATH):
            os.remove(PIPE_PATH)
        os.mkfifo(PIPE_PATH)

    def handlePress(self, key_name):
        print(f"GestureMonitor.handlePress, key_name = {key_name}")
        self.key_event_listener(key_name, True)

    def handleRelease(self, key_name):
        print(f"GestureMonitor.handleRelease, key_name = {key_name}")
        self.key_event_listener(key_name, False)

    def handleClick(self, key_name):
        print(f"GestureMonitor.handleClick, key_name = {key_name}")
        self.key_event_listener(key_name, True)
        self.key_event_listener(key_name, False)

    def run(self):
        print("GestureMonitor thread start to run")
        while True:
            with open(PIPE_PATH, "rb") as pipe:
                while True:
                    try:
                        print("GestureMonitor in while, before pipe read..")
                        event = pickle.load(pipe)
                        print(f"GestureMonitor in while, after pipe read, event: {event.name}, {event.pressed}")
                        if event.pressed:
                            self.key_detector.pressDetected(event.name)
                        else:
                            self.key_detector.releaseDetected(event.name)
                    except EOFError:
                        print("GestureMonitor in while, EOFError")
                        break
        