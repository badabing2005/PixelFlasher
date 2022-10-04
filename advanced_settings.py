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

        # Magisk Package name
        package_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        package_name_sizer.Add((20, 0), 0, 0, 5)
        package_name_label = wx.StaticText(self, label=u"Magisk Package Name:")
        self.package_name = wx.TextCtrl(self, -1, size=(300, -1))
        self.package_name.SetToolTip(u"If you have hidden Magisk,\nset this to the hidden package name.")
        self.package_name.SetValue(str(get_magisk_package()))
        package_name_sizer.Add(package_name_label, 0, wx.ALL, 5)
        package_name_sizer.Add(self.package_name, 0, wx.LEFT, 10)
        vSizer.Add(package_name_sizer, 0, wx.EXPAND, 5)

        # Check for updates options
        check_for_update_sizer = wx.BoxSizer(wx.HORIZONTAL)
        check_for_update_sizer.Add((20, 0), 0, 0, 5)
        self.check_for_update_checkbox = wx.CheckBox(self, wx.ID_ANY, u"Check for updates", wx.DefaultPosition, wx.DefaultSize, 0)
        self.check_for_update_checkbox.SetValue(get_update_check())
        self.check_for_update_checkbox.SetToolTip(u"Checks for available updates on startup")
        check_for_update_sizer.Add(self.check_for_update_checkbox, 0, wx.ALL, 5)
        vSizer.Add(check_for_update_sizer, 0, wx.EXPAND, 5)

        # Force codepage
        code_page_sizer = wx.BoxSizer(wx.HORIZONTAL)
        code_page_sizer.Add((20, 0), 0, 0, 5)
        self.force_codepage_checkbox = wx.CheckBox(self, wx.ID_ANY, u"Force codepage to:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.force_codepage_checkbox.SetValue(get_codepage_setting())
        self.force_codepage_checkbox.SetToolTip(u"Uses specified code page instead of system code page")
        self.code_page = wx.TextCtrl(self, -1, size=(300, -1))
        self.code_page.SetValue(str(get_codepage_value()))
        code_page_sizer.Add(self.force_codepage_checkbox, 0, wx.ALL, 5)
        code_page_sizer.Add(self.code_page, 0, wx.ALL, 5)
        vSizer.Add(code_page_sizer, 0, wx.EXPAND, 5)

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
        if self.advanced_options_checkbox.GetValue() != self.before:
            print(f"Setting Enable Advanced Options to: {self.advanced_options_checkbox.GetValue()}")
        set_advanced_options(self.advanced_options_checkbox.GetValue())

        if self.check_for_update_checkbox.GetValue() != get_update_check():
            print(f"Setting Check for updates to: {self.check_for_update_checkbox.GetValue()}")
        set_update_check(self.check_for_update_checkbox.GetValue())

        if self.package_name.GetValue() != '':
            if self.package_name.GetValue() != get_magisk_package():
                print(f"Setting Magisk Package Name to: {self.package_name.GetValue()}")
            set_magisk_package(self.package_name.GetValue())

        if self.force_codepage_checkbox.GetValue():
            if self.code_page.GetValue() != '' and self.code_page.GetValue().isnumeric():
                set_codepage_setting(self.force_codepage_checkbox.GetValue())
                set_codepage_value(int(self.code_page.GetValue()))
            else:
                set_codepage_setting(False)
                set_codepage_value('')
        else:
            set_codepage_setting(False)
            set_codepage_value('')
        self.EndModal(wx.ID_OK)
