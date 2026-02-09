# This file is part of PixelFlasher https://github.com/badabing2005/PixelFlasher
#
# Copyright (C) 2026 Badabing2005
# SPDX-FileCopyrightText: 2026 Badabing2005
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
import os
from datetime import datetime
from i18n import _
from runtime import (
                        load_devices_json,
                        save_devices_json,
                        delete_device,
                        update_device_custom_label,
                        toggle_device_enabled
                    )


# ============================================================================
#                            Class ManageDevicesDialog
# ============================================================================
class ManageDevicesDialog(wx.Dialog):
    def __init__(self, parent, title=_("Manage Devices")):
        super().__init__(parent, title=title, style=wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE)
        self.SetSize((1200, 600))
        self.devices = {}
        self.load_devices()
        self.init_ui()
        self.refresh_list()

    # -----------------------------------------------
    #                  load_devices
    # -----------------------------------------------
    def load_devices(self):
        self.devices = load_devices_json()

    # -----------------------------------------------
    #                  save_devices
    # -----------------------------------------------
    def save_devices(self):
        save_devices_json(self.devices)

    # -----------------------------------------------
    #                  init_ui
    # -----------------------------------------------
    def init_ui(self):
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Horizontal sizer for list and controls
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Device list (left side)
        list_box = wx.StaticBox(self, label=_("Devices"))
        list_sizer = wx.StaticBoxSizer(list_box, wx.VERTICAL)

        self.device_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.device_list.AppendColumn(_("Device ID"), width=180)
        self.device_list.AppendColumn(_("Hardware"), width=120)
        self.device_list.AppendColumn(_("Custom Label"), width=150)
        self.device_list.AppendColumn(_("Enabled"), width=100)
        self.device_list.AppendColumn(_("Connected"), width=100)
        self.device_list.AppendColumn(_("Last Seen"), width=160)

        list_sizer.Add(self.device_list, 1, wx.EXPAND | wx.ALL, 5)
        h_sizer.Add(list_sizer, 1, wx.EXPAND | wx.ALL, 5)

        # Control panel (right side)
        control_box = wx.StaticBox(self, label=_("Device Actions"))
        control_sizer = wx.StaticBoxSizer(control_box, wx.VERTICAL)

        # Selected device info
        self.selected_text = wx.StaticText(self, label=_("No device selected"))
        control_sizer.Add(self.selected_text, 0, wx.ALL, 5)
        control_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 5)

        # Custom Label section
        label_text = wx.StaticText(self, label=_("Custom Display Label:"))
        control_sizer.Add(label_text, 0, wx.ALL, 5)

        self.custom_label_ctrl = wx.TextCtrl(self)
        self.custom_label_ctrl.SetHint(_("Enter custom name"))
        self.custom_label_ctrl.SetToolTip(_("Set a custom label for this device to easily identify it in the menu.\nThis does not affect the actual device name or functionality.\ne.g., OnePlus 5 - Daily Driver"))
        control_sizer.Add(self.custom_label_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        update_label_btn = wx.Button(self, label=_("Update Label"))
        update_label_btn.Bind(wx.EVT_BUTTON, self.on_update_label)
        control_sizer.Add(update_label_btn, 0, wx.EXPAND | wx.ALL, 5)

        control_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 5)

        # Action buttons
        self.toggle_btn = wx.Button(self, label=_("Enable / Disable"))
        self.toggle_btn.Bind(wx.EVT_BUTTON, self.on_toggle_enabled)
        self.toggle_btn.Enable(False)
        control_sizer.Add(self.toggle_btn, 0, wx.EXPAND | wx.ALL, 5)

        self.delete_btn = wx.Button(self, label=_("Delete Device"))
        self.delete_btn.Bind(wx.EVT_BUTTON, self.on_delete)
        self.delete_btn.Enable(False)
        control_sizer.Add(self.delete_btn, 0, wx.EXPAND | wx.ALL, 5)

        control_sizer.AddStretchSpacer()

        # Help text
        help_text = wx.StaticText(self, label=_("Tip: Set a custom label to easily\nidentify your devices in the menu."))
        control_sizer.Add(help_text, 0, wx.ALL, 5)

        h_sizer.Add(control_sizer, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(h_sizer, 1, wx.EXPAND)

        # Bottom button sizer
        btn_sizer = wx.StdDialogButtonSizer()

        close_btn = wx.Button(self, wx.ID_CLOSE)
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        btn_sizer.AddButton(close_btn)

        btn_sizer.Realize()
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(main_sizer)

        # Bind events
        self.device_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.device_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_item_deselected)

    # -----------------------------------------------
    #                  refresh_list
    # -----------------------------------------------
    def refresh_list(self):
        self.device_list.DeleteAllItems()

        for idx, (device_id, device_data) in enumerate(sorted(self.devices.items())):
            # Device ID
            self.device_list.InsertItem(idx, device_id)

            # Hardware
            hardware = device_data.get('hardware', '') or device_data.get('device_name', '')
            self.device_list.SetItem(idx, 1, hardware)

            # Custom Label
            custom_label = device_data.get('custom_label', '')
            self.device_list.SetItem(idx, 2, custom_label)

            # Enabled
            enabled = device_data.get('enabled', True)
            self.device_list.SetItem(idx, 3, _("Yes") if enabled else _("No"))

            # Connected
            connected = device_data.get('connected', False)
            self.device_list.SetItem(idx, 4, _("Yes") if connected else _("No"))

            # Last Seen
            last_seen = device_data.get('last_seen', '')
            if last_seen:
                try:
                    # Format the datetime string
                    dt = datetime.fromisoformat(last_seen)
                    last_seen = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            self.device_list.SetItem(idx, 5, last_seen)

    # -----------------------------------------------
    #                  get_selected_device_id
    # -----------------------------------------------
    def get_selected_device_id(self):
        selected = self.device_list.GetFirstSelected()
        if selected != -1:
            return self.device_list.GetItemText(selected)
        return None

    # -----------------------------------------------
    #                  on_item_selected
    # -----------------------------------------------
    def on_item_selected(self, event):
        device_id = self.get_selected_device_id()
        if device_id and device_id in self.devices:
            device_data = self.devices[device_id]

            # Update selected text
            hardware = device_data.get('hardware', '') or device_data.get('device_name', '')
            self.selected_text.SetLabel(f"{device_id}\n({hardware})")

            # Update custom label control
            custom_label = device_data.get('custom_label', '')
            self.custom_label_ctrl.SetValue(custom_label)

            # Enable buttons
            self.toggle_btn.Enable(True)
            self.delete_btn.Enable(True)

    # -----------------------------------------------
    #                  on_item_deselected
    # -----------------------------------------------
    def on_item_deselected(self, event):
        self.selected_text.SetLabel(_("No device selected"))
        self.custom_label_ctrl.SetValue("")
        self.toggle_btn.Enable(False)
        self.delete_btn.Enable(False)

    # -----------------------------------------------
    #                  on_update_label
    # -----------------------------------------------
    def on_update_label(self, event):
        device_id = self.get_selected_device_id()
        if not device_id:
            wx.MessageBox(_("Please select a device first."), _("No Selection"), wx.OK | wx.ICON_INFORMATION)
            return

        custom_label = self.custom_label_ctrl.GetValue().strip()

        if update_device_custom_label(device_id, custom_label):
            # Update local data
            self.devices[device_id]['custom_label'] = custom_label
            self.refresh_list()

            # Reselect the item
            for i in range(self.device_list.GetItemCount()):
                if self.device_list.GetItemText(i) == device_id:
                    self.device_list.Select(i)
                    break

            wx.MessageBox(_("Custom label updated successfully."), _("Success"), wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox(_("Failed to update custom label."), _("Error"), wx.OK | wx.ICON_ERROR)

    # -----------------------------------------------
    #                  on_toggle_enabled
    # -----------------------------------------------
    def on_toggle_enabled(self, event):
        device_id = self.get_selected_device_id()
        if not device_id:
            wx.MessageBox(_("Please select a device first."), _("No Selection"), wx.OK | wx.ICON_INFORMATION)
            return

        device_data = self.devices[device_id]
        current_state = device_data.get('enabled', True)
        new_state = not current_state

        # Confirm action
        action = _("disable") if current_state else _("enable")
        result = wx.MessageBox(
            _("Are you sure you want to %s device\n%s?") % (action, device_id),
            _("Confirm %s") % action.capitalize(),
            wx.YES_NO | wx.ICON_QUESTION
        )

        if result == wx.YES:
            if toggle_device_enabled(device_id) is not None:
                # Update local data
                self.devices[device_id]['enabled'] = new_state
                self.refresh_list()

                # Reselect the item
                for i in range(self.device_list.GetItemCount()):
                    if self.device_list.GetItemText(i) == device_id:
                        self.device_list.Select(i)
                        break

                status = _("disabled") if not new_state else _("enabled")
                wx.MessageBox(_("Device %s successfully.") % status, _("Success"), wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox(_("Failed to toggle device state."), _("Error"), wx.OK | wx.ICON_ERROR)

    # -----------------------------------------------
    #                  on_delete
    # -----------------------------------------------
    def on_delete(self, event):
        device_id = self.get_selected_device_id()
        if not device_id:
            wx.MessageBox(_("Please select a device first."), _("No Selection"), wx.OK | wx.ICON_INFORMATION)
            return

        # Confirm deletion
        result = wx.MessageBox(
            _("Are you sure you want to delete the device entry for\n%s?\n\nThis will remove the device from the list, but it will be re-added on the next scan if still connected.") % device_id,
            _("Confirm Delete"),
            wx.YES_NO | wx.ICON_WARNING
        )

        if result == wx.YES:
            if delete_device(device_id):
                # Remove from local data
                del self.devices[device_id]
                self.refresh_list()

                # Clear selection
                self.selected_text.SetLabel(_("No device selected"))
                self.custom_label_ctrl.SetValue("")
                self.toggle_btn.Enable(False)
                self.delete_btn.Enable(False)

                wx.MessageBox(_("Device entry deleted successfully."), _("Success"), wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox(_("Failed to delete device entry."), _("Error"), wx.OK | wx.ICON_ERROR)

    # -----------------------------------------------
    #                  on_close
    # -----------------------------------------------
    def on_close(self, event):
        self.EndModal(wx.ID_CLOSE)
