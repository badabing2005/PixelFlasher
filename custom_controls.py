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
import wx.lib.buttons as buttons
import os
import json
import traceback
import webbrowser
import contextlib
from datetime import datetime
from runtime import get_device_images_history_file_path, detect_encoding, puml, get_phone
from i18n import _


# ============================================================================
#                               Class FilePickerComboBox
# ============================================================================
class FilePickerComboBox(wx.Panel):
    def __init__(self, parent, dialog_title=_("Select a file"), wildcard="All files (*.*)|*.*"):
        super(FilePickerComboBox, self).__init__(parent)

        self.history_file = get_device_images_history_file_path()
        self.dialog_title = dialog_title
        self.wildcard = wildcard
        self.history = []

        self.combo_box = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        self.browse_button = wx.Button(self, wx.ID_ANY, _('Browse'))

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.combo_box, 1, wx.EXPAND)
        sizer.Add(self.browse_button, 0, wx.EXPAND)
        self.SetSizer(sizer)

        self.browse_button.Bind(wx.EVT_BUTTON, self.on_browse)
        self.combo_box.Bind(wx.EVT_MOUSEWHEEL, self.on_mousewheel)

        if os.path.exists(self.history_file):
            try:
                encoding = detect_encoding(self.history_file)
                with open(self.history_file, 'r', encoding=encoding, errors="replace") as f:
                    self.history = json.load(f)
                    self.combo_box.SetItems(self.history)
            except Exception as e:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: encountered an exception during device_images_history_file loading.")
                print(f"Exception: {e}")
                print("Deleting the device_images_history_file to recover ...")
                os.remove(self.history_file)

    def SetButtonLabel(self, label):
        self.browse_button.SetLabel(label)

    def SetButtonWidth(self, width):
        current_size = self.browse_button.GetSize()
        self.browse_button.SetMinSize(wx.Size(width, current_size.GetHeight()))
        self.browse_button.SetSize(wx.Size(width, current_size.GetHeight()))

    def GetButtonWidth(self):
        return self.browse_button.GetSize().GetWidth()

    def GetPickerCtrl(self):
        # Return the browse button to make the interface compatible with wx picker controls.
        return self.browse_button

    def on_browse(self, event):
        file_dialog = wx.FileDialog(self, self.dialog_title, wildcard=self.wildcard)
        if file_dialog.ShowModal() == wx.ID_OK:
            file_path = file_dialog.GetPath()
            if file_path not in self.history:
                self.history.insert(0, file_path)
                self.combo_box.Insert(file_path, 0)
                if len(self.history) > 16:
                    self.history.pop()
                if self.combo_box.Count > 16:
                    self.combo_box.Delete(self.combo_box.Count - 1)
            self.combo_box.SetValue(file_path)
            wx.PostEvent(self.combo_box, wx.CommandEvent(wx.EVT_COMBOBOX.typeId, self.combo_box.GetId()))

    def SetPath(self, path):
        if path and path != '' and path not in self.history:
            self.history.insert(0, path)
            self.combo_box.Insert(path, 0)
            if len(self.history) > 16:
                self.history.pop()
            if self.combo_box.Count > 16:
                self.combo_box.Delete(self.combo_box.Count - 1)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f)
        self.combo_box.SetValue(path)

    def on_combo_box_change(self, event):
        path = event.GetString()
        if path == '':
            path = self.combo_box.GetValue()
        if not os.path.exists(path):
            self.history.remove(path)
            self.combo_box.Delete(self.combo_box.FindString(path))
        if path in self.history:
            self.history.remove(path)
            self.history.insert(0, path)
            self.combo_box.Delete(self.combo_box.FindString(path))
            self.combo_box.Insert(path, 0)
            self.combo_box.SetValue(path)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f)

    def Bind(self, event, handler):
        if event == wx.EVT_FILEPICKER_CHANGED:
            self.handler = handler
            self.combo_box.Bind(wx.EVT_COMBOBOX, self._on_combo_box_change)

    def _on_combo_box_change(self, event):
        self.handler(event)
        self.on_combo_box_change(event)

    def GetPath(self):
        return self.combo_box.GetStringSelection()

    def SetToolTip(self, tooltip_text):
        self.combo_box.SetToolTip(tooltip_text)

    def on_mousewheel(self, event):
        # Stop the event propagation to disable mouse wheel scrolling
        event.StopPropagation()


# ============================================================================
#                               Class NoScrollComboBox
# ============================================================================
class NoScrollComboBox(wx.ComboBox):
    def __init__(self, *args, **kwargs):
        super(NoScrollComboBox, self).__init__(*args, **kwargs)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mousewheel)

    def on_mousewheel(self, event):
        # Stop the event propagation to disable mouse wheel scrolling
        event.StopPropagation()


# ============================================================================
#                               Class NoScrollChoice
# ============================================================================
class NoScrollChoice(wx.Choice):
    def __init__(self, *args, **kwargs):
        super(NoScrollChoice, self).__init__(*args, **kwargs)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mousewheel)

    def on_mousewheel(self, event):
        # Stop the event propagation to disable mouse wheel scrolling
        event.StopPropagation()


# ============================================================================
#                               Class DropDownLink
# ============================================================================
class DropDownLink(wx.BitmapButton):
    def __init__(self, parent, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW):
        super().__init__(parent, id, bitmap, pos, size, style)
        self.Bind(wx.EVT_BUTTON, self.OnButtonClick)
        self.popup_menu = wx.Menu()

    def OnButtonClick(self, event):
        self.PopupMenu(self.popup_menu)

    def AddLink(self, label, url, icon=None):
        item = self.popup_menu.Append(wx.ID_ANY, label)
        if icon:
            item.SetBitmap(icon)
        self.Bind(wx.EVT_MENU, lambda event, url=url: self.OnLinkSelected(event, url), item)

    def OnLinkSelected(self, event, url):
        # Handle the selected link here
        print(f"Selected link: {url}")
        open_device_image_download_link(url)


# ============================================================================
#                               Class DropDownButton
# ============================================================================
class DropDownButton(buttons.GenBitmapTextButton):
    # def __init__(self, parent, id=wx.ID_ANY, label='', pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
    #     super().__init__(parent, id, wx.NullBitmap, label, pos, size, style)
    def __init__(self, parent, id, bitmap, label, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        super().__init__(parent, id, bitmap, label, pos, size, style)
        self.Bind(wx.EVT_BUTTON, self.OnButtonClick)
        self.popup_menu = wx.Menu()

    def SetBitmap(self, bitmap):
        if bitmap.IsOk():
            self.SetBitmapLabel(bitmap)
        else:
            print("Invalid bitmap")

    def OnButtonClick(self, event):
        self.PopupMenu(self.popup_menu)

    def AddFunction(self, label, function, icon_bitmap=None, enabled=True):
        item = self.popup_menu.Append(wx.ID_ANY, label)
        item.Enable(enabled)
        if icon_bitmap:
            item.SetBitmap(icon_bitmap)
        self.Bind(wx.EVT_MENU, lambda event, function=function: self.OnFunctionSelected(event, function), item)
        return item

    def OnFunctionSelected(self, event, function):
        # Call the selected function here
        function()

# ============================================================================
#                     Class ResizableButtonDirPickerCtrl
# ============================================================================
class ResizableButtonDirPickerCtrl(wx.DirPickerCtrl):
    # Custom DirPickerCtrl with ability to easily resize the browse button.

    def __init__(self, parent, id=wx.ID_ANY, path="", message="Select a folder",
                    style=wx.DIRP_USE_TEXTCTRL|wx.DIRP_DIR_MUST_EXIST,
                    button_label=None, button_width=None):
        super().__init__(parent, id, path, message, style=style)

        # Set button label if provided
        if button_label is not None:
            self.SetButtonLabel(button_label)

        # Set button width if provided
        if button_width is not None:
            self.SetButtonWidth(button_width)

    def SetButtonLabel(self, label):
        if self.GetPickerCtrl():
            self.GetPickerCtrl().SetLabel(label)

    def SetButtonWidth(self, width):
        if self.GetPickerCtrl():
            current_size = self.GetPickerCtrl().GetSize()
            self.GetPickerCtrl().SetMinSize(wx.Size(width, current_size.GetHeight()))
            self.GetPickerCtrl().SetSize(wx.Size(width, current_size.GetHeight()))

    def GetButtonWidth(self):
        if self.GetPickerCtrl():
            return self.GetPickerCtrl().GetSize().GetWidth()
        return 0

# ============================================================================
#                     Class ResizableButtonFilePickerCtrl
# ============================================================================
class ResizableButtonFilePickerCtrl(wx.FilePickerCtrl):
    # Custom FilePickerCtrl with ability to easily resize the browse button.

    def __init__(self, parent, id=wx.ID_ANY, path="", message="Select a file",
                    wildcard="All files (*.*)|*.*", style=wx.FLP_USE_TEXTCTRL,
                    button_label=None, button_width=None):
        super().__init__(parent, id, path, message, wildcard, style=style)

        # Set button label if provided
        if button_label is not None:
            self.SetButtonLabel(button_label)

        # Set button width if provided
        if button_width is not None:
            self.SetButtonWidth(button_width)

    def SetButtonLabel(self, label):
        if self.GetPickerCtrl():
            self.GetPickerCtrl().SetLabel(label)

    def SetButtonWidth(self, width):
        if self.GetPickerCtrl():
            current_size = self.GetPickerCtrl().GetSize()
            self.GetPickerCtrl().SetMinSize(wx.Size(width, current_size.GetHeight()))
            self.GetPickerCtrl().SetSize(wx.Size(width, current_size.GetHeight()))

    def GetButtonWidth(self):
        if self.GetPickerCtrl():
            return self.GetPickerCtrl().GetSize().GetWidth()
        return 0


# ============================================================================
#                    Function _open_device_image_download_link
# ============================================================================
def open_device_image_download_link(url):
    try:
        with contextlib.suppress(Exception):
            device = get_phone()
            if device:
                hardware = device.hardware
            else:
                hardware = ''
        print(f"Launching browser for Google image download URL: {url}#{hardware}")
        webbrowser.open_new(f"{url}#{hardware}")
        puml(f":Open Link;\nnote right\n=== {hardware} Firmware Link\n[[{url}#{hardware}]]\nend note\n", True)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening firmware link")
        traceback.print_exc()
