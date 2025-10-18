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
from i18n import _


# ============================================================================
#                               Class DeviceSelectorDialog
# ============================================================================
class DeviceSelectorDialog(wx.Dialog):

    # ============================================================================
    #                               Function __init__
    # ============================================================================
    def __init__(self, parent, devices, title=_("Select Device"), message=_("Select a device:")):
        super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.devices = devices
        self.selected_device = None

        self._create_ui(message)
        self._bind_events()
        self._size_and_center()

    # ============================================================================
    #                               Function _create_ui
    # ============================================================================
    def _create_ui(self, message):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Message
        message_label = wx.StaticText(self, label=message)
        main_sizer.Add(message_label, 0, wx.ALL | wx.EXPAND, 10)

        # Device list
        self.device_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.device_list.AppendColumn("Device", width=200)
        self.device_list.AppendColumn("Filename", width=500)

        # Populate the list
        for i, device in enumerate(self.devices):
            index = self.device_list.InsertItem(i, device.get('device', 'Unknown'))
            self.device_list.SetItem(index, 1, device.get('zip_filename', 'Unknown'))
            self.device_list.SetItemData(index, i)

        # Select first item by default
        if self.devices:
            self.device_list.Select(0)

        main_sizer.Add(self.device_list, 1, wx.ALL | wx.EXPAND, 10)

        # Buttons
        button_sizer = wx.StdDialogButtonSizer()

        ok_button = wx.Button(self, wx.ID_OK, _("OK"))
        ok_button.SetDefault()
        button_sizer.AddButton(ok_button)

        cancel_button = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        button_sizer.AddButton(cancel_button)

        button_sizer.Realize()
        main_sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        self.SetSizer(main_sizer)

    # ============================================================================
    #                               Function _bind_events
    # ============================================================================
    def _bind_events(self):
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)

    # ============================================================================
    #                               Function _size_and_center
    # ============================================================================
    def _size_and_center(self):
        self.SetSize((750, 850))
        self.CenterOnParent()

    # ============================================================================
    #                               Function on_item_activated
    # ============================================================================
    def on_item_activated(self, event):
        # Handle double-click on list item
        self.EndModal(wx.ID_OK)

    # ============================================================================
    #                               Function on_ok
    # ============================================================================
    def on_ok(self, event):
        selection = self.device_list.GetFirstSelected()
        if selection != -1:
            device_index = self.device_list.GetItemData(selection)
            self.selected_device = self.devices[device_index]
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox(_("Please select a device."), _("No Selection"), wx.OK | wx.ICON_WARNING, self)

    # ============================================================================
    #                               Function get_selected_device
    # ============================================================================
    def get_selected_device(self):
        return self.selected_device


# ============================================================================
#                               Function show_device_selector
# ============================================================================
def show_device_selector(parent, devices, title=_("Select Device"), message=_("Select a device:")):
    """
    Show device selector dialog and return selected device.

    Args:
        parent: Parent window
        devices: List of device dictionaries with 'device', 'zip_filename', 'url' keys
        title: Dialog title
        message: Message to display above the list

    Returns:
        Selected device dictionary or None if cancelled
    """
    if not devices:
        wx.MessageBox(_("No devices available."), _("Error"), wx.OK | wx.ICON_ERROR, parent)
        return None

    dialog = DeviceSelectorDialog(parent, devices, title, message)

    try:
        if dialog.ShowModal() == wx.ID_OK:
            return dialog.get_selected_device()
        else:
            return None
    finally:
        dialog.Destroy()
