from PyQt5 import QtWidgets
from tivo_rcu_ui import Ui_TivoRcuDlg
from key_event_name import *


class TivoRcuDlg(QtWidgets.QDialog):
    def __init__(self, key_event_listener):
        super(TivoRcuDlg, self).__init__()
        self.ui = Ui_TivoRcuDlg()
        self.ui.setupUi(self)
        self.setup_control()
        self.key_event_listener = key_event_listener

    def setup_control(self):
        self.ui.mPower.clicked.connect(self.powerClicked)
        self.ui.mDPadLeft.clicked.connect(self.dpadLeftClicked)
        self.ui.mDPadRight.clicked.connect(self.dpadRightClicked)
        self.ui.mDPadUp.clicked.connect(self.dpadUpClicked)
        self.ui.mDPadDown.clicked.connect(self.dpadDownClicked)
        self.ui.mDPadOk.clicked.connect(self.dpadOkClicked)
        self.ui.mBack.clicked.connect(self.backClicked)
        self.ui.mVolUp.clicked.connect(self.volUpClicked)
        self.ui.mVolDown.clicked.connect(self.volDownClicked)
        self.ui.mTivo.clicked.connect(self.tivoClicked)
        self.ui.mNum0.clicked.connect(self.num0Clicked)
        self.ui.mNum1.clicked.connect(self.num1Clicked)
        self.ui.mNum2.clicked.connect(self.num2Clicked)
        self.ui.mNum3.clicked.connect(self.num3Clicked)
        self.ui.mNum4.clicked.connect(self.num4Clicked)
        self.ui.mNum5.clicked.connect(self.num5Clicked)
        self.ui.mNum6.clicked.connect(self.num6Clicked)
        self.ui.mNum7.clicked.connect(self.num7Clicked)
        self.ui.mNum8.clicked.connect(self.num8Clicked)
        self.ui.mNum9.clicked.connect(self.num9Clicked)

    def powerClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_POWER)

    def dpadLeftClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_LEFT)

    def dpadRightClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_RIGHT)

    def dpadUpClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_UP)

    def dpadDownClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_DOWN)

    def dpadOkClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_SEL)

    def volUpClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_VOLUP)

    def volDownClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_VOLDW)

    def backClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_BACK)

    def tivoClicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_TIVO)

    def num0Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_0)

    def num1Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_1)

    def num2Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_2)

    def num3Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_3)

    def num4Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_4)

    def num5Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_5)

    def num6Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_6)

    def num7Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_7)

    def num8Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_8)

    def num9Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_9)
