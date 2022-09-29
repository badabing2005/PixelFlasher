#!/usr/bin/env python

import wx
from runtime import *

# ============================================================================
#                               Class MessageBox
# ============================================================================
class MessageBox(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        self.SetTitle(get_message_box_title())

        vSizer = wx.BoxSizer(wx.VERTICAL)
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))
        self.message_label.Label = get_message_box_message()
        message_sizer.Add(self.message_label, 1, wx.ALL|wx.EXPAND, 20)
        vSizer.Add(message_sizer, 1, wx.EXPAND, 5)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        self.ok_button = wx.Button(self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        buttons_sizer.Add(self.ok_button, 0, wx.ALL, 20)
        self.cancel_button = wx.Button(self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 20)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        vSizer.Add(buttons_sizer, 0, wx.EXPAND, 5)

        self.SetSizer(vSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        self.ok_button.Bind(wx.EVT_BUTTON, self._onOk)
        self.cancel_button.Bind(wx.EVT_BUTTON, self._onCancel)

        # Autosize the dialog
        self.SetSizerAndFit(vSizer)

    def __del__(self):
        pass

    def _onCancel(self, e):
        self.EndModal(wx.ID_CANCEL)

    def _onOk(self, e):
        self.EndModal(wx.ID_OK)

