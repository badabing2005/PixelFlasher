#!/usr/bin/env python

import wx
import wx.lib.mixins.listctrl as listmix
from runtime import *


# ============================================================================
#                               Class ListCtrl
# ============================================================================
class ListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
#                               Class MagiskModules
# ============================================================================
class MagiskModules(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        self.SetTitle("Manage Magisk Modules")

        vSizer = wx.BoxSizer(wx.VERTICAL)
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.Label = "When you press the OK button, the Modules with checkbox selected will be enabled and the rest will be disabled."
        if sys.platform == "win32":
            self.message_label.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.message_label.SetForegroundColour(wx.Colour(255, 0, 0))

        message_sizer.Add(self.message_label, 0, wx.ALL, 20)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        vSizer.Add(message_sizer, 0, wx.EXPAND, 5)

        device = get_phone()
        modules = device.magisk_detailed_modules

        list_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.list  = ListCtrl(self, -1, size=(-1, self.CharHeight * 18), style = wx.LC_REPORT)

        self.list.InsertColumn(0, 'Name', width = -1)
        self.list.InsertColumn(1, 'Version', wx.LIST_FORMAT_LEFT, -1)
        self.list.InsertColumn(2, 'Description', wx.LIST_FORMAT_LEFT,  -1)
        if sys.platform == "win32":
            self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLUE'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10).Bold())))

        self.list.EnableCheckBoxes()

        i = 0
        for module in modules:
            if module.id == '':
                index = self.list.InsertItem(i, module.name)
            else:
                index = self.list.InsertItem(i, module.id)
            if module.version == '':
                self.list.SetItem(index, 1, module.versionCode)
            else:
                self.list.SetItem(index, 1, module.version)
            self.list.SetItem(index, 2, module.description)
            if module.state == 'enabled':
                self.list.CheckItem(index, check=True)
            i += 1

        self.list.SetColumnWidth(0, -2)
        grow_column(self.list, 0, 20)
        self.list.SetColumnWidth(1, -2)
        grow_column(self.list, 1, 20)
        self.list.SetColumnWidth(2, -2)
        grow_column(self.list, 2, 20)

        list_sizer.Add(self.list, 1, wx.ALL|wx.EXPAND, 10)

        vSizer.Add(list_sizer , 1, wx.EXPAND, 5)

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
        self.list.PostSizeEventToParent()
        self.SetSizerAndFit(vSizer)
        a = self.list.GetViewRect()
        self.SetSize(vSizer.MinSize.Width + 120, vSizer.MinSize.Height + 140)

        print("\nOpening Magisk Modules Manager ...")

    # -----------------------------------------------
    #                  __del__
    # -----------------------------------------------
    def __del__(self):
        pass

    # -----------------------------------------------
    #                  _onCancel
    # -----------------------------------------------
    def _onCancel(self, e):
        self.EndModal(wx.ID_CANCEL)

    # -----------------------------------------------
    #                  _onOk
    # -----------------------------------------------
    def _onOk(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
        device = get_phone()
        modules = device.magisk_detailed_modules
        for i in range(0, self.list.ItemCount, 1):
            if modules[i].state == 'enabled':
                module_state = True
            else:
                module_state = False
            list_state = self.list.IsItemChecked(i)

            if list_state == module_state:
                print(f"Module: {modules[i].name:<36} state has not changed,   Nothing to do. [Kept {modules[i].state.upper()}]")
            elif list_state:
                print(f"Module: {modules[i].name:<36} state has changed,       ENABLING  the module ...")
                res = device.enable_magisk_module(modules[i].dirname)
                if res == 0:
                    modules[i].state = 'enabled'
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to disable module: {modules[i].name}")
            else:
                print(f"Module: {modules[i].name:<36} state has changed,       DISABLING the module ...")
                res = device.disable_magisk_module(modules[i].dirname)
                if res == 0:
                    modules[i].state = 'disbled'
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to disable module: {modules[i].name}")
        print('')
        self.EndModal(wx.ID_OK)
