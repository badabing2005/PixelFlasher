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
        self.SetSize(800, 500)
        self.before = get_advanced_options()

        vSizer = wx.BoxSizer( wx.VERTICAL )
        warning_sizer = wx.BoxSizer( wx.HORIZONTAL )
        warning_text = '''WARNING!
This is advanced configuration.
Unless you know what you are doing,
you should not be enabling it.

YOU AND YOU ALONE ARE RESPONSIBLE FOR ANYTHING THAT HAPPENS TO YOUR DEVICE.
THIS TOOL IS CODED WITH THE EXPRESS ASSUMPTION THAT YOU ARE FAMILIAR WITH
ADB, MAGISK, ANDROID, AND ROOT.
IT IS YOUR RESPONSIBILITY TO ENSURE THAT YOU KNOW WHAT YOU ARE DOING.
'''
        self.warning_label = wx.StaticText( self, wx.ID_ANY, warning_text, wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL )
        self.warning_label.Wrap( -1 )
        self.warning_label.SetForegroundColour( wx.Colour( 255, 0, 0 ) )
        warning_sizer.Add( self.warning_label, 1, wx.ALL, 10 )
        staticline = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )

        vSizer.Add( warning_sizer, 1, wx.EXPAND, 5 )
        vSizer.Add( staticline, 0, wx.EXPAND, 5 )
        vSizer.Add( ( 0, 20), 0, 0, 5 )

        advanced_options_sizer = wx.BoxSizer( wx.HORIZONTAL )
        advanced_options_sizer.Add( ( 20, 0), 0, 0, 5 )
        self.advanced_options_checkbox = wx.CheckBox( self, wx.ID_ANY, u"Enable Advanced Options", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.advanced_options_checkbox.SetValue(get_advanced_options())
        self.advanced_options_checkbox.SetToolTip( u"Expert mode" )
        advanced_options_sizer.Add( self.advanced_options_checkbox, 0, wx.ALL, 5 )
        vSizer.Add( advanced_options_sizer, 0, wx.EXPAND, 5 )

        reset_sizer = wx.BoxSizer( wx.HORIZONTAL )
        reset_sizer.Add( ( 20, 0), 1, wx.EXPAND, 5 )
        self.reset_button = wx.Button( self, wx.ID_ANY, u"Reset", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.reset_button.SetToolTip( u"Reset to default values." )
        self.reset_button.Hide()
        reset_sizer.Add( self.reset_button, 0, wx.ALL, 5 )
        vSizer.Add( reset_sizer, 1, wx.EXPAND, 5 )

        buttons_sizer = wx.BoxSizer( wx.HORIZONTAL )
        buttons_sizer.Add( ( 100, 0), 0, 0, 5 )
        self.ok_button = wx.Button( self, wx.ID_ANY, u"OK", wx.Point( -1,-1 ), wx.DefaultSize, 0 )
        buttons_sizer.Add( self.ok_button, 0, wx.ALL, 5 )
        buttons_sizer.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.cancel_button = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.cancel_button.SetDefault()
        buttons_sizer.Add( self.cancel_button, 0, wx.ALL, 5 )
        buttons_sizer.Add( ( 100, 0), 0, 0, 5 )
        vSizer.Add( buttons_sizer, 1, wx.EXPAND, 5 )

        self.SetSizer( vSizer )
        self.Layout()

        # Connect Events
        self.ok_button.Bind( wx.EVT_BUTTON, self._onOk )
        self.cancel_button.Bind( wx.EVT_BUTTON, self._onCancel )
        self.reset_button.Bind( wx.EVT_BUTTON, self._onReset )

    def _onReset(self, e):
        set_advanced_options(False)
        self.advanced_options_checkbox.SetValue( False )

    def _onCancel(self, e):
        set_advanced_options(self.before)
        self.EndModal(wx.ID_CANCEL)

    def _onOk(self, e):
        set_advanced_options(self.advanced_options_checkbox.GetValue())
        self.EndModal(wx.ID_OK)

    def get_advanced_settings(self):
        return self.advanced_options_checkbox.GetValue()
