#!/usr/bin/python3
from threading import Timer

KEY_STATE_TO_DETERMINE = 'KEY_STATE_TO_DETERMINE'
KEY_STATE_PRESSED = 'KEY_STATE_PRESSED'


class KeyDetector():
    def __init__(self, handlePress, handleRelease, handleClick):
        self.handlePress = handlePress
        self.handleRelease = handleRelease
        self.handleClick = handleClick
        self.key_state_keeper = None
        self.detect_key_timer = None
        # threshold to determine if a key press-release is a click or or press/hold, in seconds
        self.detect_key_threshold = 0.5

    def detectKeyTimeout(self, key_name):
        print(f'KeyDetector.detectKeyTimeout: {key_name}')
        if self.key_state_keeper is None or key_name not in self.key_state_keeper:
            print(f'KeyDetector.detectKeyTimeout is not valid with {key_name}')
            return
        key_state = self.key_state_keeper[key_name]
        if key_state == KEY_STATE_TO_DETERMINE:
            self.handlePress(key_name)
            self.key_state_keeper[key_name] = KEY_STATE_PRESSED
        else:
            print(
                f'KeyDetector.detectKeyTimeout, {key_name} with state: {key_state} is not valid')

    def onPressed(self, key_name):
        if self.key_state_keeper == None:
            self.key_state_keeper = {key_name: KEY_STATE_TO_DETERMINE}
            self.detect_key_timer = Timer(
                self.detect_key_threshold, self.detectKeyTimeout, args=(key_name,))
            self.detect_key_timer.start()
        else:
            print(
                f'KeyDetector.onPressed error: previous {key_name} onPressed has not get onReleased yet, ignore!')

    def onReleased(self, key_name):
        self.detect_key_timer.cancel()
        self.detect_key_timer = None

        key_state = self.key_state_keeper[key_name]
        if key_state == KEY_STATE_TO_DETERMINE:
            self.handleClick(key_name)
        elif key_state == KEY_STATE_PRESSED:
            self.handleRelease(key_name)
        self.key_state_keeper = None
