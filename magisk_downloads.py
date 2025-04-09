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

import webbrowser
from urllib.parse import urlparse

import pyperclip
import darkdetect
import markdown
import traceback
import wx
import wx.html
import wx.lib.mixins.listctrl as listmix
import wx.lib.wxpTag

import images as images
from runtime import *


# ============================================================================
#                               Class HtmlWindow
# ============================================================================
class HtmlWindow(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())

# ============================================================================
#                               Class ListCtrl
# ============================================================================
class ListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
#                               Class MagiskDownloads
# ============================================================================
class MagiskDownloads(wx.Dialog):
    def __init__(self, *args, **kwargs):
        style = kwargs.get('style', wx.DEFAULT_DIALOG_STYLE) | wx.RESIZE_BORDER
        kwargs['style'] = style
        wx.Dialog.__init__(self, *args, **kwargs)
        self.SetTitle("Download and Install Rooting Application")
        self.url =  None
        self.channel = None
        self.version = None
        self.versionCode = None
        self.filename = None
        self.release_notes = None
        self.package = None

        vSizer = wx.BoxSizer(wx.VERTICAL)
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.Label = "Select rooting app to install."
        if sys.platform == "win32":
            self.message_label.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))

        message_sizer.Add(self.message_label, 0, wx.ALL, 20)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        vSizer.Add(message_sizer, 0, wx.EXPAND, 5)

        list_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # list control
        if self.CharHeight > 20:
            self.il = wx.ImageList(24, 24)
            self.idx1 = self.il.Add(images.official_24.GetBitmap())
        else:
            self.il = wx.ImageList(16, 16)
            self.idx1 = self.il.Add(images.official_16.GetBitmap())
        self.list  = ListCtrl(self, -1, size=(-1, self.CharHeight * 18), style = wx.LC_REPORT)
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        device = get_phone(True)
        if not device:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device to be able to install.")
            print("You can still download the rooting app, but you will not be able to install it.")
            self.Parent.clear_device_selection()

        apks = get_magisk_apks()

        max_url_column_width = 600
        self.list.InsertColumn(0, 'Root App', width = -1)
        self.list.InsertColumn(1, 'Version', wx.LIST_FORMAT_LEFT, -1)
        self.list.InsertColumn(2, 'VersionCode', wx.LIST_FORMAT_LEFT,  -1)
        self.list.InsertColumn(3, 'URL', wx.LIST_FORMAT_LEFT, -1)
        self.list.SetColumnWidth(3, min(self.list.GetColumnWidth(3), max_url_column_width))
        self.list.InsertColumn(4, 'Package', wx.LIST_FORMAT_LEFT,  -1)
        if sys.platform == "win32":
            self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLUE'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10).Bold())))

        i = 0
        for apk in apks:
            if apk.type:
                index = self.list.InsertItem(i, apk.type)
                if apk.type in ('stable', 'beta', 'canary', 'debug'):
                    self.list.SetItemColumnImage(i, 0, 0)
                else:
                    self.list.SetItemColumnImage(i, 0, -1)
            if apk.version:
                self.list.SetItem(index, 1, apk.version)
            if apk.versionCode:
                self.list.SetItem(index, 2, apk.versionCode)
            if apk.link:
                self.list.SetItem(index, 3, apk.link)
            if apk.package:
                self.list.SetItem(index, 4, apk.package)
            i += 1

        self.list.SetColumnWidth(0, -2)
        grow_column(self.list, 0, 20)
        self.list.SetColumnWidth(1, -2)
        grow_column(self.list, 1, 20)
        self.list.SetColumnWidth(2, -2)
        grow_column(self.list, 2, 20)
        self.list.SetColumnWidth(3, -2)
        grow_column(self.list, 3, 20)
        self.list.SetColumnWidth(3, min(self.list.GetColumnWidth(3), max_url_column_width))  # Set maximum width after growing
        self.list.SetColumnWidth(4, -1)
        grow_column(self.list, 4, 20)

        list_sizer.Add(self.list, 1, wx.ALL|wx.EXPAND, 10)

        vSizer.Add(list_sizer , 0, wx.EXPAND, 5)

        # Release Notes
        self.html = HtmlWindow(self, wx.ID_ANY, size=(420, -1))
        if darkdetect.isDark():
            black_html = "<!DOCTYPE html>\n<html><body style=\"background-color:#1e1e1e;\"></body></html>"
            self.html.SetPage(black_html)
        if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo:
            self.html.SetStandardFonts()
        vSizer.Add(self.html , 1, wx.EXPAND | wx.ALL, 10)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        self.install_button = wx.Button(self, wx.ID_ANY, u"Install", wx.DefaultPosition, wx.DefaultSize, 0)
        self.install_button.SetToolTip(u"WARNING! Do not install magisk if you already have a hidden (stub) Magisk installed.\nFirst unhide Magisk before attempting an install.")
        self.install_button.Enable(False)
        buttons_sizer.Add(self.install_button, 0, wx.ALL, 20)

        self.download_button = wx.Button(self, wx.ID_ANY, u"Download", wx.DefaultPosition, wx.DefaultSize, 0)
        self.download_button.SetToolTip(u"Download the rooting app.")
        self.download_button.Enable(False)
        buttons_sizer.Add(self.download_button, 0, wx.ALL, 20)

        self.cancel_button = wx.Button(self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 20)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        vSizer.Add(buttons_sizer, 0, wx.EXPAND, 5)

        self.SetSizer(vSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        self.install_button.Bind(wx.EVT_BUTTON, self._onOk)
        self.download_button.Bind(wx.EVT_BUTTON, self._OnDownloadMagisk)
        self.cancel_button.Bind(wx.EVT_BUTTON, self._onCancel)
        self.list.Bind(wx.EVT_LEFT_DOWN, self._on_apk_selected)
        self.list.Bind(wx.EVT_RIGHT_DOWN, self._onRightDown)
        # for wxMSW
        self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self._onRightClick)
        # for wxGTK
        self.list.Bind(wx.EVT_RIGHT_UP, self._onRightClick)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._onItemSelected, self.list)


        # Autosize the dialog
        self.list.PostSizeEventToParent()
        self.SetSizerAndFit(vSizer)
        a = self.list.GetViewRect()
        self.SetSize(vSizer.MinSize.Width + 80, vSizer.MinSize.Height + 420)

        print("\nOpening Root App Installer / Downloader ...")
        puml(f":Open Root App Installer / Downloader;\n", True)


    # -----------------------------------------------
    #                  _onItemSelected
    # -----------------------------------------------
    def _onItemSelected(self, event):
        self.currentItem = event.Index
        print(f"Magisk {self.list.GetItemText(self.currentItem)} is selected.")
        puml(f":Select Magisk {self.list.GetItemText(self.currentItem)};\n")
        event.Skip()

    # -----------------------------------------------
    #                  _onRightDown
    # -----------------------------------------------
    def _onRightDown(self, event):
        x = event.GetX()
        y = event.GetY()
        # print("x, y = %s\n" % str((x, y)))
        item, flags = self.list.HitTest((x, y))
        if item != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
            self.list.Select(item)
        event.Skip()

    # -----------------------------------------------
    #                  _onRightClick
    # -----------------------------------------------
    def _onRightClick(self, event):
        # print("OnRightClick %s\n" % self.list.GetItemText(self.currentItem))

        # only do this part the first time so the events are only bound once
        if not hasattr(self, "popupDisable"):
            self.popupCopyURL = wx.NewIdRef()
            self.popupCopyPackageId = wx.NewIdRef()
            self.popupDownloadMagisk = wx.NewIdRef()

            self.Bind(wx.EVT_MENU, self._OnCopyURL, id=self.popupCopyURL)
            self.Bind(wx.EVT_MENU, self._OnCopyPackageId, id=self.popupCopyPackageId)
            self.Bind(wx.EVT_MENU, self._OnDownloadMagisk, id=self.popupDownloadMagisk)

        # build the menu
        menu = wx.Menu()
        menu.Append(self.popupCopyURL, "Copy URL to Clipboard")
        menu.Append(self.popupCopyPackageId, "Copy Package ID to Clipboard")
        menu.Append(self.popupDownloadMagisk, "Download Selected Rooting App")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    # -----------------------------------------------
    #                  _OnCopyPackageId
    # -----------------------------------------------
    def _OnCopyPackageId(self, event):
        item = self.list.GetItem(self.currentItem, 4)
        pyperclip.copy(item.Text)

    # -----------------------------------------------
    #                  _OnCopyURL
    # -----------------------------------------------
    def _OnCopyURL(self, event):
        item = self.list.GetItem(self.currentItem, 3)
        pyperclip.copy(item.Text)

    # -----------------------------------------------
    #                  _OnDownloadMagisk
    # -----------------------------------------------
    def _OnDownloadMagisk(self, event):
        url = self.list.GetItem(self.currentItem, 3).Text
        version = self.list.GetItem(self.currentItem, 1).Text
        versionCode = self.list.GetItem(self.currentItem, 2).Text
        app = self.channel.replace(' ', '_')
        filename = f"{app}_{version}_{versionCode}.apk"
        dialog = wx.FileDialog(None, "Save File", defaultFile=filename, wildcard="All files (*.*)|*.*", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            destination_path = dialog.GetPath()
            print(f"Downloading {destination_path} from {url}...")
            download_file(url=url, filename=destination_path, callback=None, stream=False)

    # -----------------------------------------------
    #                  __del__
    # -----------------------------------------------
    def __del__(self):
        pass

    # -----------------------------------------------
    #                  _onCancel
    # -----------------------------------------------
    def _onCancel(self, e):
        puml(f":Cancelled Magisk Downloader/Installer;\n", True)
        self.EndModal(wx.ID_CANCEL)

    # -----------------------------------------------
    #                  _on_apk_selected
    # -----------------------------------------------
    def _on_apk_selected(self, e):
        x,y = e.GetPosition()
        row,flags = self.list.HitTest((x,y))
        for i in range (0, self.list.ItemCount):
            # deselect all items
            self.list.Select(i, 0)
            item = self.list.GetItem(i)
            # reset colors
            if sys.platform == "win32":
                item.SetTextColour(wx.BLACK)
            elif darkdetect.isDark():
                item.SetTextColour(wx.WHITE)
            self.list.SetItem(item)
        if row != -1:
            self.list.Select(row)
            item = self.list.GetItem(row)
            if sys.platform == "win32":
                item.SetTextColour(wx.BLUE)
            self.list.SetItem(item)
            self.channel = self.list.GetItemText(row, col=0)
            self.version = self.list.GetItemText(row, col=1)
            self.versionCode = self.list.GetItemText(row, col=2)
            self.url = self.list.GetItemText(row, col=3)
            self.filename = os.path.basename(urlparse(self.url).path)
            self.package = self.list.GetItemText(row, col=4)
            device = get_phone()
            apks = get_magisk_apks()
            self.download_button.Enable(True)
            release_notes = apks[row].release_notes
            # convert markdown to html
            self.release_notes = markdown.markdown(release_notes)
            self.html.SetPage(self.release_notes)
            if device:
                self.install_button.Enable(True)
        else:
            self.install_button.Enable(False)
            self.download_button.Enable(False)

    # -----------------------------------------------
    #                  _onOk
    # -----------------------------------------------
    def _onOk(self, e):
        proceed = True
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
        app = self.channel.replace(' ', '_')
        filename = f"{app}_{self.version}_{self.versionCode}.apk"
        device = get_phone(True)
        if not device:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device to be able to install.")
            return

        if 'Namelesswonder' in self.url and not device.has_init_boot:
            print(f"WARNING: The selected Magisk is not supported for your device: {device.hardware}")
            print("         Only Pixel 7 (panther) and Pixel 7 Pro (cheetah) and Pixel 7a (lynx) and Pixel Tablet (tangorpro) are currently supported.")
            print("         See details at: https://xdaforums.com/t/magisk-magisk-zygote64_32-enabling-32-bit-support-for-apps.4521029/")

            title = "Device Not Supported"
            message =  f"ERROR: Your phone model is: {device.hardware}\n\n"
            message += "The selected Magisk is not supported for your device\n"
            message += "Only Pixel 7 (panther) and Pixel 7 Pro (cheetah) and Pixel 7a (lynx) and Pixel Tablet (tangorpro) are currently supported.\n\n"
            message += "Unless you know what you are doing, if you choose to continue\n"
            message += "you risk running into serious issues, proceed only if you are absolutely\n"
            message += "certain that this is what you want, you have been warned.\n\n"
            message += "Click OK to accept and continue.\n"
            message += "or Hit CANCEL to abort."
            print(f"\n*** Dialog ***\n{message}\n______________\n")
            # puml(":Dialog;\n")
            # puml(f"note right\n{message}\nend note\n")
            dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                print("User pressed ok.")
                # puml(":User Pressed OK;\n")
            else:
                print("User pressed cancel.")
                print("Aborting ...\n")
                # puml("#pink:User Pressed Cancel to abort;\n}\n")
                proceed = False
        if proceed:
            self._on_spin('start')
            print(f"Downloading {app}: {self.channel} version: {self.version} versionCode: {self.versionCode} ...")
            download_file(self.url, filename)
            config_path = get_config_path()
            app = os.path.join(config_path, 'tmp', filename)
            device.install_apk(app, fastboot_included = True)
            # Fresh install of Magisk, reset the package name to default value
            if self.package in [MAGISK_PKG_NAME, MAGISK_ALPHA_PKG_NAME, MAGISK_DELTA_PKG_NAME]:
                set_magisk_package(self.package)
                self.Parent.config.magisk = self.package
            print('')
            self._on_spin('stop')
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
