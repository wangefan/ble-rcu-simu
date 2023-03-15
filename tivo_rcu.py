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
        self.ui.mNum1.clicked.connect(self.num1Clicked)

    # override
    def closeEvent(self, event):
        print("TivoRcuDlg.closeEvent")
        event.ignore()

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

    def num1Clicked(self):
        if self.key_event_listener != None:
            self.key_event_listener(KEY_EVENT_NAME_1)
