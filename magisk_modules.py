#!/usr/bin/env python

import wx
import wx.lib.mixins.listctrl as listmix
import traceback
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
        self.SetTitle("Manage Magisk")

        # Message label
        self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.Label = "When you press the OK button, the Modules with checkbox selected will be enabled and the rest will be disabled."
        if sys.platform == "win32":
            self.message_label.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.message_label.SetForegroundColour(wx.Colour(255, 0, 0))

        # Module label
        modules_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=u"Magisk Modules")
        modules_label.SetToolTip(u"Enable / Disable Magisk modules")

        # Modules list
        self.list  = ListCtrl(self, -1, size=(-1, self.CharHeight * 18), style = wx.LC_REPORT)
        self.PopulateList()

        # Ok button
        self.ok_button = wx.Button(self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)

        # Install module button
        self.install_module_button = wx.Button(self, wx.ID_ANY, u"Install Module", wx.DefaultPosition, wx.DefaultSize, 0)
        self.install_module_button.SetToolTip(u"Install magisk module.")

        # Enable zygisk button
        self.enable_zygisk_button = wx.Button(self, wx.ID_ANY, u"Enable Zygisk", wx.DefaultPosition, wx.DefaultSize, 0)
        self.enable_zygisk_button.SetToolTip(u"Enable Magisk zygisk (requires reboot)")

        # Disable zygisk button
        self.disable_zygisk_button = wx.Button(self, wx.ID_ANY, u"Disable Zygisk", wx.DefaultPosition, wx.DefaultSize, 0)
        self.disable_zygisk_button.SetToolTip(u"Disable Magisk zygisk (requires reboot)")

        # Enable denlylist button
        self.enable_denylist_button = wx.Button(self, wx.ID_ANY, u"Enable Denylist", wx.DefaultPosition, wx.DefaultSize, 0)
        self.enable_denylist_button.SetToolTip(u"Enable Magisk denylist")

        # Disable denylist button
        self.disable_denylist_button = wx.Button(self, wx.ID_ANY, u"Disable Denylist", wx.DefaultPosition, wx.DefaultSize, 0)
        self.disable_denylist_button.SetToolTip(u"Disable Magisk denylist")

        # Cancel button
        self.cancel_button = wx.Button(self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)

        # Label for managing denylist and SU Permissions
        management_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=u"To manage denylist or to manage SU permissions, use PixelFlasher's App Manager feature.")
        management_label.SetToolTip(u"Use Pixelflasher's App Manager functionality to add/remove items to denylist or su permissions.")
        font = management_label.GetFont()
        font.SetStyle(wx.FONTSTYLE_ITALIC)
        management_label.SetFont(font)

        # Sizers
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        message_sizer.Add(self.message_label, 0, wx.ALL, 20)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        #
        list_sizer = wx.BoxSizer(wx.HORIZONTAL)
        list_sizer.Add(self.list, 1, wx.ALL|wx.EXPAND, 10)
        #
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        buttons_sizer.Add(self.ok_button, 0, wx.ALL, 20)
        buttons_sizer.Add(self.install_module_button, 0, wx.ALL, 20)
        buttons_sizer.Add(self.enable_zygisk_button, 0, wx.ALL, 20)
        buttons_sizer.Add(self.disable_zygisk_button, 0, wx.ALL, 20)
        buttons_sizer.Add(self.enable_denylist_button, 0, wx.ALL, 20)
        buttons_sizer.Add(self.disable_denylist_button, 0, wx.ALL, 20)
        buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 20)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        #
        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.Add(message_sizer, 0, wx.EXPAND, 5)
        vSizer.Add(modules_label, 0, wx.LEFT, 10)
        vSizer.Add(list_sizer , 1, wx.EXPAND, 5)
        vSizer.Add(management_label, 0, wx.LEFT, 10)
        vSizer.Add(buttons_sizer, 0, wx.EXPAND, 5)

        self.SetSizer(vSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        self.ok_button.Bind(wx.EVT_BUTTON, self._onOk)
        self.install_module_button.Bind(wx.EVT_BUTTON, self._onInstallModule)
        self.enable_zygisk_button.Bind(wx.EVT_BUTTON, self._onEnableZygisk)
        self.disable_zygisk_button.Bind(wx.EVT_BUTTON, self._onDisableZygisk)
        self.enable_denylist_button.Bind(wx.EVT_BUTTON, self._onEnableDenylist)
        self.disable_denylist_button.Bind(wx.EVT_BUTTON, self._onDisableDenylist)
        self.cancel_button.Bind(wx.EVT_BUTTON, self._onCancel)

        # Autosize the dialog
        self.list.PostSizeEventToParent()
        self.SetSizerAndFit(vSizer)
        a = self.list.GetViewRect()
        self.SetSize(vSizer.MinSize.Width + 120, vSizer.MinSize.Height + 140)

        print("\nOpening Magisk Modules Manager ...")

    # -----------------------------------------------
    #              Function PopulateList
    # -----------------------------------------------
    def PopulateList(self, refresh=False):
        device = get_phone()
        modules = device.get_magisk_detailed_modules(refresh)

        self.list.InsertColumn(0, 'Name', width = -1)
        self.list.InsertColumn(1, 'Version', wx.LIST_FORMAT_LEFT, -1)
        self.list.InsertColumn(2, 'Description', wx.LIST_FORMAT_LEFT,  -1)
        if sys.platform == "win32":
            self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLUE'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10).Bold())))

        self.list.EnableCheckBoxes()

        if modules:
            i = 0
            for module in modules:
                if module.id == '':
                    if len(modules) == 1:
                        continue
                    else:
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
    #                  _onEnableZygisk
    # -----------------------------------------------
    def _onEnableZygisk(self, e):
        print("Enable Zygisk")
        device = get_phone()
        device.magisk_enable_zygisk(True)

    # -----------------------------------------------
    #                  _onDisableZygisk
    # -----------------------------------------------
    def _onDisableZygisk(self, e):
        print("Disable Zygisk")
        device = get_phone()
        device.magisk_enable_zygisk(False)

    # -----------------------------------------------
    #                  _onEnableDenylist
    # -----------------------------------------------
    def _onEnableDenylist(self, e):
        print("Enable Denylist")
        device = get_phone()
        device.magisk_enable_denylist(True)

    # -----------------------------------------------
    #                  _onDisableDenylist
    # -----------------------------------------------
    def _onDisableDenylist(self, e):
        print("Disable Denylist")
        device = get_phone()
        device.magisk_enable_denylist(False)

    # -----------------------------------------------
    #                  _onInstallModule
    # -----------------------------------------------
    def _onInstallModule(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Install Module.")
        with wx.FileDialog(self, "select Module file to install", '', '', wildcard="Magisk Modules (*.*.zip)|*.zip", style=wx.FD_OPEN) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                print("User cancelled module install.")
                return
            # save the current contents in the file
            device = get_phone()
            pathname = fileDialog.GetPath()
            print(f"\nSelected {pathname} for installation.")
            try:
                self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
                device.install_magisk_module(pathname)
                self.list.ClearAll()
                self.PopulateList(True)
                self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            except IOError:
                wx.LogError(f"Cannot install module file '{pathname}'.")
                traceback.print_exc()

    # -----------------------------------------------
    #                  _onOk
    # -----------------------------------------------
    def _onOk(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
        device = get_phone()
        modules = device.get_magisk_detailed_modules()
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
