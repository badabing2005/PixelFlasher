#!/usr/bin/env python

import wx
from runtime import *

# ============================================================================
#                               Class AdvancedSettings
# ============================================================================
class AdvancedSettings(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        self.SetTitle("Advanced Configuration Settings")
        self.before = get_advanced_options()

        vSizer = wx.BoxSizer(wx.VERTICAL)
        warning_sizer = wx.BoxSizer(wx.HORIZONTAL)
        warning_text = '''WARNING!
This is advanced configuration.
Unless you know what you are doing,
you should not be enabling it.

YOU AND YOU ALONE ARE RESPONSIBLE FOR ANYTHING THAT HAPPENS TO YOUR DEVICE.
THIS TOOL IS CODED WITH THE EXPRESS ASSUMPTION THAT YOU ARE FAMILIAR WITH
ADB, MAGISK, ANDROID, AND ROOT.
IT IS YOUR RESPONSIBILITY TO ENSURE THAT YOU KNOW WHAT YOU ARE DOING.
'''
        # warning label
        self.warning_label = wx.StaticText(self, wx.ID_ANY, warning_text, wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL)
        self.warning_label.Wrap(-1)
        self.warning_label.SetForegroundColour(wx.Colour(255, 0, 0))
        warning_sizer.Add(self.warning_label, 1, wx.ALL, 10)
        vSizer.Add(warning_sizer, 1, wx.EXPAND, 5)

        # advanced options
        advanced_options_sizer = wx.BoxSizer(wx.HORIZONTAL)
        advanced_options_sizer.Add((20, 0), 0, 0, 5)
        self.advanced_options_checkbox = wx.CheckBox(self, wx.ID_ANY, u"Enable Advanced Options", wx.DefaultPosition, wx.DefaultSize, 0)
        self.advanced_options_checkbox.SetValue(get_advanced_options())
        self.advanced_options_checkbox.SetToolTip(u"Expert mode")
        advanced_options_sizer.Add(self.advanced_options_checkbox, 0, wx.ALL, 5)
        vSizer.Add(advanced_options_sizer, 0, wx.EXPAND, 5)

        # static line
        staticline = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        vSizer.Add(staticline, 0, wx.EXPAND, 5)

        # gap
        vSizer.Add((0, 20), 0, 0, 5)

        # Check for updates options
        check_for_update_sizer = wx.BoxSizer(wx.HORIZONTAL)
        check_for_update_sizer.Add((20, 0), 0, 0, 5)
        self.check_for_update_checkbox = wx.CheckBox(self, wx.ID_ANY, u"Check for updates", wx.DefaultPosition, wx.DefaultSize, 0)
        self.check_for_update_checkbox.SetValue(get_update_check())
        self.check_for_update_checkbox.SetToolTip(u"Checks for available updates on startup")
        check_for_update_sizer.Add(self.check_for_update_checkbox, 0, wx.ALL, 5)
        vSizer.Add(check_for_update_sizer, 0, wx.EXPAND, 5)

        # gap
        vSizer.Add((0, 20), 0, 0, 5)

        # buttons
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

        # Connect Events
        self.ok_button.Bind(wx.EVT_BUTTON, self._onOk)
        self.cancel_button.Bind(wx.EVT_BUTTON, self._onCancel)

        # Autosize the dialog
        self.SetSizerAndFit(vSizer)

    def _onCancel(self, e):
        set_advanced_options(self.before)
        self.EndModal(wx.ID_CANCEL)

    def _onOk(self, e):
        set_advanced_options(self.advanced_options_checkbox.GetValue())
        set_update_check(self.check_for_update_checkbox.GetValue())
        self.EndModal(wx.ID_OK)

    def get_advanced_settings(self):
        return self.advanced_options_checkbox.GetValue()

    def get_check_for_update_settings(self):
        return self.check_for_update_checkbox.GetValue()
