#!/usr/bin/env python

# This file is part of PixelFlasher https://github.com/badabing2005/PixelFlasher
#
# Copyright (C) 2025 Badabing2005
# SPDX-FileCopyrightText: 2025 Badabing2005
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Also add information on how to contact you by electronic and paper mail.
#
# If your software can interact with users remotely through a computer network,
# you should also make sure that it provides a way for users to get its source.
# For example, if your program is a web application, its interface could
# display a "Source" link that leads users to an archive of the code. There are
# many ways you could offer source, and different solutions will be better for
# different programs; see section 13 for the specific requirements.
#
# You should also get your employer (if you work as a programmer) or school, if
# any, to sign a "copyright disclaimer" for the program, if necessary. For more
# information on this, and how to apply and follow the GNU AGPL, see
# <https://www.gnu.org/licenses/>.

import wx
import wx.lib.mixins.listctrl as listmix
import traceback
import images as images
import darkdetect
import markdown
import wx.html
import webbrowser
from datetime import datetime
from runtime import *
from constants import *
from message_box_ex import MessageBoxEx
from i18n import _


# ============================================================================
#                               Class HtmlWindow
# ============================================================================
class HtmlWindow(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())

    def CopySelectedText(self):
        selection = self.SelectionToText()
        if selection:
            data = wx.TextDataObject()
            data.SetText(selection)
            clipboard = wx.Clipboard.Get()
            clipboard.Open()
            clipboard.SetData(data)
            clipboard.Close()

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
    def __init__(self, *args, parent=None, config=None, **kwargs):
        if config:
            size = (config.magisk_width, config.magisk_height)
        else:
            size=(MAGISK_WIDTH, MAGISK_HEIGHT)

        wx.Dialog.__init__(self, parent, *args, **kwargs, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size=size)

        self.device = get_phone(True)
        if not self.device:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device.")
            wx.MessageBox(_("❌ ERROR: You must first select a valid device."), _("Error"), wx.OK | wx.ICON_ERROR)
            self.Close()
            return

        self.config = config
        self.SetTitle(_("Manage Magisk"))
        self.pif_json_path = PIF_JSON_PATH

        # Instance variable to store current selected module
        self.module = None
        self.pi_app = 'gr.nikolasspyr.integritycheck'
        self.coords = Coords()

        # Message label
        self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.Label = _("When you press the OK button, the Modules with checkbox selected will be enabled and the rest will be disabled.")
        if sys.platform == "win32":
            self.message_label.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.message_label.SetForegroundColour(wx.Colour(255, 0, 0))

        # Module label
        self.modules_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=_("Magisk Modules"))
        self.modules_label.SetToolTip(_("Enable / Disable Magisk modules"))
        font = wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.modules_label.SetFont(font)

        # Modules list control
        if self.CharHeight > 20:
            self.il = wx.ImageList(24, 24)
            self.idx1 = self.il.Add(images.download_24.GetBitmap())
        else:
            self.il = wx.ImageList(16, 16)
            self.idx1 = self.il.Add(images.download_16.GetBitmap())
        self.list  = ListCtrl(self, -1, size=(-1, self.CharHeight * 18), style = wx.LC_REPORT | wx.LC_SINGLE_SEL )
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        # Change Log
        self.html = HtmlWindow(self, wx.ID_ANY, size=(-1, 320))
        if darkdetect.isDark():
            black_html = "<!DOCTYPE html>\n<html><body style=\"background-color:#1e1e1e;\"></body></html>"
            self.html.SetPage(black_html)
        if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo:
            self.html.SetStandardFonts()

        # Ok button
        self.ok_button = wx.Button(self, wx.ID_ANY, _("OK"), wx.DefaultPosition, wx.DefaultSize, 0)

        # Install module button
        self.install_module_button = wx.Button(self, wx.ID_ANY, _("Install Module"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.install_module_button.SetToolTip(_("Install magisk module."))

        # update module button
        self.update_module_button = wx.Button(self, wx.ID_ANY, _("Update Module"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.update_module_button.SetToolTip(_("Update magisk module."))
        self.update_module_button.Enable(False)

        # UnInstall module button
        self.uninstall_module_button = wx.Button(self, wx.ID_ANY, _("Uninstall Module"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.uninstall_module_button.SetToolTip(_("Uninstall magisk module."))
        self.uninstall_module_button.Enable(False)

        # Run Module Action button
        self.run_action_button = wx.Button(self, wx.ID_ANY, _("Run Action"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.run_action_button.SetToolTip(_("Run Module action.sh."))
        self.run_action_button.Enable(False)

        # Play Integrity Fix Install button
        self.pif_install_button = wx.Button(self, wx.ID_ANY, _("Install Pif / TS / TargetedFix Module"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.pif_install_button.SetToolTip(_("Install Play Integrity Fix related modules."))

        # ZygiskNext Install button
        self.zygisk_next_install_button = wx.Button(self, wx.ID_ANY, _("Install ZygiskNext Module"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.zygisk_next_install_button.SetToolTip(_("Install ZygiskNext module."))

        # Systemless hosts button
        self.systemless_hosts_button = wx.Button(self, wx.ID_ANY, _("Systemless Hosts"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.systemless_hosts_button.SetToolTip(_("Add Systemless Hosts Module."))

        # Enable zygisk button
        self.enable_zygisk_button = wx.Button(self, wx.ID_ANY, _("Enable Zygisk"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.enable_zygisk_button.SetToolTip(_("Enable Magisk zygisk (requires reboot)"))

        # Disable zygisk button
        self.disable_zygisk_button = wx.Button(self, wx.ID_ANY, _("Disable Zygisk"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.disable_zygisk_button.SetToolTip(_("Disable Magisk zygisk (requires reboot)"))

        # Enable denlylist button
        self.enable_denylist_button = wx.Button(self, wx.ID_ANY, _("Enable Denylist"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.enable_denylist_button.SetToolTip(_("Enable Magisk denylist"))

        # Disable denylist button
        self.disable_denylist_button = wx.Button(self, wx.ID_ANY, _("Disable Denylist"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.disable_denylist_button.SetToolTip(_("Disable Magisk denylist"))

        # Superuser Access button
        self.superuser_access_button = wx.Button(self, wx.ID_ANY, _("Superuser Access"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.superuser_access_button.SetToolTip(_("Superuser Access (requires reboot)"))

        # Refresh
        self.refresh_button = wx.Button(self, wx.ID_ANY, _("Refresh"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.refresh_button.SetToolTip(_("Refresh Magisk modules list."))

        # static line
        self.staticline1 = wx.StaticLine(parent=self, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LI_HORIZONTAL)

        # Cancel button
        self.cancel_button = wx.Button(self, wx.ID_ANY, _("Cancel"), wx.DefaultPosition, wx.DefaultSize, 0)

        # Make the buttons the same size
        button_width = self.pif_install_button.GetSize()[0] + 10
        self.install_module_button.SetMinSize((button_width, -1))
        self.update_module_button.SetMinSize((button_width, -1))
        self.uninstall_module_button.SetMinSize((button_width, -1))
        self.run_action_button.SetMinSize((button_width, -1))
        self.pif_install_button.SetMinSize((button_width, -1))
        self.zygisk_next_install_button.SetMinSize((button_width, -1))
        self.systemless_hosts_button.SetMinSize((button_width, -1))
        self.enable_zygisk_button.SetMinSize((button_width, -1))
        self.disable_zygisk_button.SetMinSize((button_width, -1))
        self.enable_denylist_button.SetMinSize((button_width, -1))
        self.disable_denylist_button.SetMinSize((button_width, -1))
        self.superuser_access_button.SetMinSize((button_width, -1))
        self.refresh_button.SetMinSize((button_width, -1))

        # Label for managing denylist and SU Permissions
        management_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=_("To manage denylist or to manage SU permissions, use PixelFlasher's App Manager feature."))
        management_label.SetToolTip(_("Use Pixelflasher's App Manager functionality to add/remove items to denylist or su permissions."))
        font = management_label.GetFont()
        font.SetStyle(wx.FONTSTYLE_ITALIC)
        management_label.SetFont(font)

        # populate the list
        res = self.PopulateList()
        if res == -1:
            self.Close()
            return
        self.add_magisk_details()

        # Sizers
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        message_sizer.Add(self.message_label, 0, wx.ALL, 20)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        h_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        h_buttons_sizer.Add(self.ok_button, 0, wx.ALL, 20)
        h_buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 20)
        h_buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        v_buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        v_buttons_sizer.Add(self.install_module_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.update_module_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.uninstall_module_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.run_action_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.pif_install_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.zygisk_next_install_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.systemless_hosts_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.enable_zygisk_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.disable_zygisk_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.enable_denylist_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.disable_denylist_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.superuser_access_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.refresh_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.staticline1, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.AddStretchSpacer()

        modules_sizer = wx.BoxSizer(wx.VERTICAL)
        modules_sizer.Add(self.list, 1, wx.EXPAND | wx.ALL, 10)
        modules_sizer.Add(self.html, 0, wx.EXPAND | wx.ALL, 10)

        outside_modules_sizer = wx.BoxSizer(wx.HORIZONTAL)
        outside_modules_sizer.Add(modules_sizer, 1, wx.EXPAND | wx.ALL, 0)
        outside_modules_sizer.Add(v_buttons_sizer, 0, wx.EXPAND | wx.ALL, 0)

        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.Add(message_sizer, 0, wx.EXPAND, 5)
        vSizer.Add(self.modules_label, 0, wx.LEFT, 10)
        vSizer.Add(outside_modules_sizer, 1, wx.EXPAND, 0)
        vSizer.Add(management_label, 0, wx.LEFT, 10)
        vSizer.Add(h_buttons_sizer, 0, wx.EXPAND, 5)

        self.SetSizer(vSizer)
        self.SetMinSize((400, 300))
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        self.ok_button.Bind(wx.EVT_BUTTON, self.onOk)
        self.install_module_button.Bind(wx.EVT_BUTTON, self.onInstallModule)
        self.update_module_button.Bind(wx.EVT_BUTTON, self.onUpdateModule)
        self.uninstall_module_button.Bind(wx.EVT_BUTTON, self.onUninstallModule)
        self.run_action_button.Bind(wx.EVT_BUTTON, self.onRunModuleAction)
        self.pif_install_button.Bind(wx.EVT_BUTTON, self.onInstallPif)
        self.zygisk_next_install_button.Bind(wx.EVT_BUTTON, self.onInstallZygiskNext)
        self.systemless_hosts_button.Bind(wx.EVT_BUTTON, self.onSystemlessHosts)
        self.enable_zygisk_button.Bind(wx.EVT_BUTTON, self.onEnableZygisk)
        self.disable_zygisk_button.Bind(wx.EVT_BUTTON, self.onDisableZygisk)
        self.enable_denylist_button.Bind(wx.EVT_BUTTON, self.onEnableDenylist)
        self.disable_denylist_button.Bind(wx.EVT_BUTTON, self.onDisableDenylist)
        self.superuser_access_button.Bind(wx.EVT_BUTTON, self.onSuperuserAccess)
        self.refresh_button.Bind(wx.EVT_BUTTON, self.onRefresh)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.onCancel)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected, self.list)
        self.html.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu)
        self.list.Bind(wx.EVT_LEFT_DOWN, self.onModuleSelection)
        self.Bind(wx.EVT_SIZE, self.OnResize)

        # Autosize the dialog
        # self.list.PostSizeEventToParent()
        # self.SetSizerAndFit(vSizer)
        # a = self.list.GetViewRect()
        # self.SetSize(vSizer.MinSize.Width + 120, vSizer.MinSize.Height + 140)

        print("\nOpening Magisk Modules Manager ...")

    # -----------------------------------------------
    #              Function PopulateList
    # -----------------------------------------------
    def PopulateList(self, refresh=False):
        modules = self.device.get_magisk_detailed_modules(refresh)

        self.pif_install_button.Enable(True)

        self.list.InsertColumn(0, 'ID', width = -1)
        self.list.InsertColumn(1, 'Name', width = -1)
        self.list.InsertColumn(2, 'Version', wx.LIST_FORMAT_LEFT, -1)
        self.list.InsertColumn(3, 'VersionCode', wx.LIST_FORMAT_LEFT, -1)
        self.list.InsertColumn(4, 'Description', wx.LIST_FORMAT_LEFT,  -1)
        if sys.platform == "win32":
            self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLUE'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10).Bold())))

        self.list.EnableCheckBoxes()
        if modules:
            i = 0
            for module in modules:
                if module.id == '' and module.name == '' or module.dirname == '*':
                    continue
                if module.id == '':
                    if len(modules) == 1:
                        continue
                    else:
                        index = self.list.InsertItem(i, module.dirname)
                else:
                    index = self.list.InsertItem(i, module.id)

                # disable pif button if it is already installed.
                if module.id == "playintegrityfix" and "Play Integrity" in module.name:
                    if module.name == "Play Integrity Fork":
                        self.pif_json_path = '/data/adb/modules/playintegrityfix/custom.pif.json'
                    elif module.name == "tricky_store":
                        self.pif_json_path = '/data/adb/tricky_store/spoof_build_vars'
                    elif module.name != "Play Integrity NEXT":
                        self.pif_json_path = '/data/adb/pif.json'
                    if module.version in ["PROPS-v2.1", "PROPS-v2.0"]:
                        self.pif_json_path = '/data/adb/modules/playintegrityfix/pif.json'

                # disable Systemless Hosts button if it is already installed.
                if module.id == "hosts" and module.name == "Systemless Hosts":
                    self.systemless_hosts_button.Enable(False)

                # disable denylist if Magisk is delta
                if get_magisk_package() == MAGISK_DELTA_PKG_NAME:
                    self.enable_denylist_button.Enable(False)
                    self.disable_denylist_button.Enable(False)

                # disable button if self.device is not rooted.
                if not self.device.rooted:
                    self.install_module_button.Enable(False)
                    self.update_module_button.Enable(False)
                    self.uninstall_module_button.Enable(False)
                    self.run_action_button.Enable(False)
                    self.pif_install_button.Enable(False)
                    self.zygisk_next_install_button.Enable(False)
                    self.enable_zygisk_button.Enable(False)
                    self.disable_zygisk_button.Enable(False)
                    self.systemless_hosts_button.Enable(False)
                    self.enable_denylist_button.Enable(False)
                    self.disable_denylist_button.Enable(False)
                    self.superuser_access_button.Enable(False)
                    self.refresh_button.Enable(False)

                self.list.SetItemColumnImage(i, 0, -1)
                with contextlib.suppress(Exception):
                    if module.updateAvailable:
                        self.list.SetItemColumnImage(i, 0, 0)

                self.list.SetItem(index, 1, module.name)
                self.list.SetItem(index, 2, module.version)
                self.list.SetItem(index, 3, module.versionCode)
                self.list.SetItem(index, 4, module.description)

                if module.state == 'enabled':
                    self.list.CheckItem(index, check=True)
                elif module.state == 'remove':
                    self.list.SetItemTextColour(index, wx.LIGHT_GREY)

                i += 1

        self.list.SetColumnWidth(0, -2)
        grow_column(self.list, 0, 20)
        self.list.SetColumnWidth(1, -2)
        grow_column(self.list, 1, 20)
        self.list.SetColumnWidth(2, -2)
        grow_column(self.list, 2, 20)
        self.list.SetColumnWidth(3, -2)
        grow_column(self.list, 3, 20)
        self.list.SetColumnWidth(4, -2)
        grow_column(self.list, 4, 20)

    # -----------------------------------------------
    #                  add_magisk_details
    # -----------------------------------------------
    def add_magisk_details(self):
        device = get_phone()
        if not device:
            return

        data = f"Magisk Manager Version:  {device.magisk_app_version}\n"
        if device.rooted:
            data += f"Magisk Version:          {device.magisk_version}\n"
        data += "\nMagisk Modules"
        self.modules_label.SetLabel(data)

    # -----------------------------------------------
    #                  __del__
    # -----------------------------------------------
    def __del__(self):
        pass

    # -----------------------------------------------
    #                  onModuleSelection
    # -----------------------------------------------
    def onModuleSelection(self, event):
        x,y = event.GetPosition()
        row,flags = self.list.HitTest((x,y))
        if row == -1:
            self.uninstall_module_button.Enable(False)
            self.uninstall_module_button.SetLabel(_('Uninstall Module'))
            self.run_action_button.Enable(False)
        else:
            self.uninstall_module_button.Enable(True)
            if self.list.GetItemTextColour(row) == wx.LIGHT_GREY:
                self.uninstall_module_button.SetLabel(_('Restore Module'))
            else:
                self.uninstall_module_button.SetLabel(_('Uninstall Module'))
        event.Skip()

    # -----------------------------------------------
    #                  onItemSelected
    # -----------------------------------------------
    def onItemSelected(self, event):
        self.currentItem = event.Index
        device = get_phone()
        if not device.rooted:
            return
        print(f"Magisk Module {self.list.GetItemText(self.currentItem)} is selected.")
        # puml(f":Select Magisk Module {self.list.GetItemText(self.currentItem)};\n")

        # Get the module object for the selected item
        modules = device.get_magisk_detailed_modules(refresh=False)
        self.module = modules[self.currentItem]
        self.html.SetPage('')
        if self.module.updateAvailable:
            self.update_module_button.Enable(True)
        if self.module.updateDetails and self.module.updateDetails.changelog:
            changelog_md = f"# Change Log:\n{self.module.updateDetails.changelog}"
            self.outputMessage(changelog_md)
        else:
            self.update_module_button.Enable(False)
        # if module has has_action then enable run action button
        if self.module.hasAction == 'True':
            self.run_action_button.Enable(True)
        else:
            self.run_action_button.Enable(False)
        event.Skip()

    # -----------------------------------------------
    #                  outputMessage
    # -----------------------------------------------
    def outputMessage(self, md_message):
        self.html.SetPage('')
        # convert markdown to html
        html_message = markdown.markdown(md_message)
        self.html.SetPage(html_message)

    # -----------------------------------------------
    #                  onCancel
    # -----------------------------------------------
    def onCancel(self, e):
        self.EndModal(wx.ID_CANCEL)

    # -----------------------------------------------
    #                  onEnableZygisk
    # -----------------------------------------------
    def onEnableZygisk(self, e):
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            print("Enable Zygisk")
            self._on_spin('start')
            res = device.magisk_enable_zygisk(True)
            if res == 0:
                self.outputMessage(_("## You need to reboot your device for the changes to take effect."))
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in function onEnableZygisk")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onDisableZygisk
    # -----------------------------------------------
    def onDisableZygisk(self, e):
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            print("Disable Zygisk")
            self._on_spin('start')
            res = device.magisk_enable_zygisk(False)
            if res == 0:
                self.outputMessage(_("## You need to reboot your device for the changes to take effect."))
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in function onDisableZygisk")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onEnableDenylist
    # -----------------------------------------------
    def onEnableDenylist(self, e):
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            print("Enable Denylist")
            self._on_spin('start')
            device.magisk_enable_denylist(True)
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in function onEnableDenylist")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onDisableDenylist
    # -----------------------------------------------
    def onDisableDenylist(self, e):
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            print("Disable Denylist")
            self._on_spin('start')
            device.magisk_enable_denylist(False)
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in function onDisableDenylist")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onSuperuserAccess
    # -----------------------------------------------
    def onSuperuserAccess(self, e):
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            buttons_text = [_("Disabled"), _("Apps Only"), _("ADB Only"), _("Apps and ADB"), _("Cancel")]
            dlg = MessageBoxEx(parent=self, title=_('Magisk'), message=_("Superuser Access"), button_texts=buttons_text, default_button=1)
            dlg.CentreOnParent(wx.BOTH)
            result = dlg.ShowModal()
            dlg.Destroy()
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed {buttons_text[result -1]}")
            value = None
            if result <= 4:
                value = str(result - 1)
            else:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
                print("Aborting ...\n")
                return -1

            self._on_spin('start')
            debug(f"Superuser Access: {value}")
            res = device.magisk_modify_root_access(value)
            if res == 0:
                self.outputMessage(_("## You need to reboot your device for the changes to take effect."))
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in function onSuperuserAccess")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onRefresh
    # -----------------------------------------------
    def onRefresh(self, e):
        self.refresh_modules()

    # -----------------------------------------------
    #                  onSystemlessHosts
    # -----------------------------------------------
    def onSystemlessHosts(self, e):
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            print("Add Systemless Hosts")
            self._on_spin('start')
            device.magisk_add_systemless_hosts()
            self.refresh_modules()
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in function onSystemlessHosts")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onInstallPif
    # -----------------------------------------------
    def onInstallPif(self, e):
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            buttons_text = [_("osm0sis PlayIntegrityFork"), "TrickyStore", "TargetedFix", _("Cancel")]
            dlg = MessageBoxEx(parent=self, title=_('PIF Module'), message=_("Select the module you want to install"), button_texts=buttons_text, default_button=1)
            dlg.CentreOnParent(wx.BOTH)
            result = dlg.ShowModal()
            dlg.Destroy()
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed {buttons_text[result -1]}")
            module_update_url = None
            gh_latest_url = None
            if result == 1:
                module_update_url = OSM0SIS_PIF_UPDATE_URL
            elif result == 2:
                # module_update_url = TRICKYSTORE_UPDATE_URL
                gh_latest_url = get_gh_latest_release_asset_regex('5ec1cff', 'TrickyStore', r'^Tricky\-Store.*\-release\.zip$')
            elif result == 3:
                module_update_url = TARGETEDFIX_UPDATE_URL
                # gh_latest_url = get_gh_latest_release_asset_regex('VisionR1', 'TargetedFix', r'^TargetedFix.*\.zip$')
                # gh_latest_url = get_gh_pre_release_asset_regex('VisionR1', 'TargetedFix', r'^TargetedFix.*\.zip$')
            else:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
                print("Aborting ...\n")
                return -1

            url = None
            if gh_latest_url is not None:
                url = gh_latest_url
            elif module_update_url is not None:
                url_obj = check_module_update(module_update_url)
                url = url_obj.zipUrl
            if url is None or url == '':
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get module download link.")
                print("Aborting ...\n")
                return -1

            self._on_spin('start')
            downloaded_file_path = download_file(url)
            print(f"Installing Play Integrity Fix (PIF) module. URL: {downloaded_file_path} ...")
            res = device.magisk_install_module(downloaded_file_path)
            if res == 0:
                self.outputMessage(_("## You need to reboot your device to complete the installation."))
            self.refresh_modules()
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Play Integrity Fix module installation.")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onInstallZygiskNext
    # -----------------------------------------------
    def onInstallZygiskNext(self, e):
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            module_update_url = ZYGISK_NEXT_UPDATE_URL
            url = check_module_update(module_update_url)
            if url is None:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get module download link.")
                print("Aborting ...\n")
                return -1

            self._on_spin('start')
            downloaded_file_path = download_file(url.zipUrl)
            print(f"Installing ZygiskNext module. URL: {downloaded_file_path} ...")
            res = device.magisk_install_module(downloaded_file_path)
            if res == 0:
                self.outputMessage(_("## You need to reboot your device to complete the installation."))
            self.refresh_modules()
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during ZygiskNext module installation.")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onRunModuleAction
    # -----------------------------------------------
    def onRunModuleAction(self, e):
        # run the action.sh script
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            self._on_spin('start')
            res = device.magisk_run_module_action(self.module.dirname)
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk modules run action.")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onUninstallModule
    # -----------------------------------------------
    def onUninstallModule(self, e):
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            id = self.list.GetItem(self.currentItem, 0).Text
            name = self.list.GetItem(self.currentItem, 1).Text
            modules = device.get_magisk_detailed_modules()
            self._on_spin('start')
            for i in range(0, self.list.ItemCount, 1):
                if modules[i].dirname == id:
                    if modules[i].state == 'remove':
                        print(f"Restoring Module {name} ...")
                        res = device.restore_magisk_module(modules[i].dirname)
                    else:
                        print(f"Uninstalling Module {name} ...")
                        res = device.magisk_uninstall_module(modules[i].dirname)
                    if res == 0:
                        modules[i].state = 'remove'
                        self.refresh_modules()
                        self.outputMessage(_("## You need to reboot your device for the changes to take effect."))
                    else:
                        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to remove module: {modules[i].name}")
                    break
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk modules uninstall")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onUpdateModule
    # -----------------------------------------------
    def onUpdateModule(self, e):
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            id = self.list.GetItem(self.currentItem, 0).Text
            name = self.list.GetItem(self.currentItem, 1).Text
            print(f"Updating Module {name} ...")
            if self.module and self.module.updateAvailable and self.module.updateDetails and (self.module.id and self.module.id == id) and (self.module.name and self.module.name == name):
                url = self.module.updateDetails.zipUrl
                self._on_spin('start')
                print(f"Downloading Magisk Module: {name} URL: {url} ...")
                downloaded_file_path = download_file(url)
                res = device.magisk_install_module(downloaded_file_path)
                if res == 0:
                    self.outputMessage(_("## You need to reboot your device to complete the update."))
            self.refresh_modules()
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk modules update")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onInstallModule
    # -----------------------------------------------
    def onInstallModule(self, e):
        device = get_phone(True)
        if not device.rooted:
            return
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Install Module.")
        with wx.FileDialog(self, "_(select Module file to install)", '', '', wildcard="Magisk Modules (*.*.zip)|*.zip", style=wx.FD_OPEN) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                print("User cancelled module install.")
                return
            # save the current contents in the file
            pathname = fileDialog.GetPath()
            print(f"\nSelected {pathname} for installation.")
            try:
                self._on_spin('start')
                res = device.magisk_install_module(pathname)
                if res == 0:
                    self.outputMessage(_("## You need to reboot your device to complete the installation."))
                self.refresh_modules()
            except IOError:
                wx.LogError(f"Cannot install module file '{pathname}'.")
                traceback.print_exc()
            finally:
                self._on_spin('stop')

    # -----------------------------------------------
    #                  onContextMenu
    # -----------------------------------------------
    def onContextMenu(self, event):
        menu = wx.Menu()
        copy_item = menu.Append(wx.ID_COPY, _("Copy"))
        select_all_item = menu.Append(wx.ID_SELECTALL, _("Select All"))
        self.Bind(wx.EVT_MENU, self.onCopy, copy_item)
        self.Bind(wx.EVT_MENU, self.onSelectAll, select_all_item)

        self.PopupMenu(menu)
        menu.Destroy()

    # -----------------------------------------------
    #                  onCopy
    # -----------------------------------------------
    def onCopy(self, event):
        self.html.CopySelectedText()

    # -----------------------------------------------
    #                  onSelectAll
    # -----------------------------------------------
    def onSelectAll(self, event):
        self.html.SelectAll()

    # -----------------------------------------------
    #                  onOk
    # -----------------------------------------------
    def onOk(self, e):
        device = get_phone(True)
        if not device.rooted:
            self.EndModal(wx.ID_OK)
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
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
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to disable module: {modules[i].name}")
            else:
                print(f"Module: {modules[i].name:<36} state has changed,       DISABLING the module ...")
                res = device.disable_magisk_module(modules[i].dirname)
                if res == 0:
                    modules[i].state = 'disabled'
                else:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to disable module: {modules[i].name}")
        print('')
        self.EndModal(wx.ID_OK)

    # -----------------------------------------------
    #                  _on_spin
    # -----------------------------------------------
    def _on_spin(self, state):
        wx.YieldIfNeeded()
        if state == 'start':
            self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
            self.Parent._on_spin('start')
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            self.Parent._on_spin('stop')

    # ----------------------------------------------------------------------------
    #                               refresh_modules
    # ----------------------------------------------------------------------------
    def refresh_modules(self):
        # self.Freeze()
        self.list.ClearAll()
        self.PopulateList(True)
        # self.Thaw

    # -----------------------------------------------
    #                  OnResize
    # -----------------------------------------------
    def OnResize(self, event):
        self.resizing = True
        self.Parent.config.magisk_width = self.Rect.Width
        self.Parent.config.magisk_height = self.Rect.Height

        self.Layout()
        event.Skip(True)

