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

# ============================================================================
#                      Class KsuAssetSelectorDialog
# ============================================================================
class KsuAssetSelectorDialog(wx.Dialog):
    def __init__(self, parent, assets, title="Select KSU Asset", message="Select a KSU asset:", suggested_asset=None):
        super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.assets = assets
        self.selected_asset = None

        self.init_ui(message, suggested_asset)
        self.Centre()

    def init_ui(self, message, suggested_asset):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Message
        message_text = wx.StaticText(self, label=message)
        main_sizer.Add(message_text, 0, wx.ALL | wx.EXPAND, 10)

        # Asset list
        self.asset_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.asset_list.AppendColumn("Asset Name", width=500)
        self.asset_list.AppendColumn("Version", width=100)
        self.asset_list.AppendColumn("Size", width=120)

        # Populate list
        for i, asset in enumerate(self.assets):
            index = self.asset_list.InsertItem(i, asset['name'])
            # Extract version from asset name if possible
            import re
            match = re.search(r'\.([0-9]+)(?:_.*|)-', asset['name'])
            version = match.group(1) if match else "Unknown"
            self.asset_list.SetItem(index, 1, version)

            # Format size
            size_bytes = asset.get('size', 0)
            if size_bytes > 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            elif size_bytes > 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes} B"
            self.asset_list.SetItem(index, 2, size_str)

            # Select suggested asset
            if suggested_asset and asset['name'] == suggested_asset['name']:
                self.asset_list.Select(index)
                self.asset_list.Focus(index)

        main_sizer.Add(self.asset_list, 1, wx.ALL | wx.EXPAND, 10)

        # Suggested text
        if suggested_asset:
            suggested_text = wx.StaticText(self, label=f"Suggested: {suggested_asset['name']}")
            suggested_text.SetFont(suggested_text.GetFont().Bold())
            main_sizer.Add(suggested_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Buttons
        button_sizer = wx.StdDialogButtonSizer()

        ok_button = wx.Button(self, wx.ID_OK, "OK")
        ok_button.SetDefault()
        button_sizer.AddButton(ok_button)

        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")
        button_sizer.AddButton(cancel_button)

        button_sizer.Realize()
        main_sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 10)

        self.SetSizer(main_sizer)

        # Check screen size and adjust dialog size if needed
        display = wx.Display()
        screen_size = display.GetGeometry().GetSize()

        # Desired size
        desired_width = 780
        desired_height = 950

        # Leave some margin from screen edges
        margin = 50
        max_width = screen_size.width - (margin * 2)
        max_height = screen_size.height - (margin * 2)

        # Adjust size to fit screen
        final_width = min(desired_width, max_width)
        final_height = min(desired_height, max_height)

        self.SetSize((final_width, final_height))

        # Bind events
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        self.asset_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)

    def on_ok(self, event):
        selected_index = self.asset_list.GetFirstSelected()
        if selected_index != -1:
            self.selected_asset = self.assets[selected_index]
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox("Please select an asset.", "No Selection", wx.OK | wx.ICON_WARNING)

    def on_item_activated(self, event):
        self.selected_asset = self.assets[event.GetIndex()]
        self.EndModal(wx.ID_OK)

    def get_selected_asset(self):
        return self.selected_asset


# ============================================================================
#                  Function show_ksu_asset_selector
# ============================================================================
def show_ksu_asset_selector(parent, assets, title="Select KSU Asset", message="Select a KSU asset:", suggested_asset=None):
    dialog = KsuAssetSelectorDialog(parent, assets, title, message, suggested_asset)

    if dialog.ShowModal() == wx.ID_OK:
        selected_asset = dialog.get_selected_asset()
        dialog.Destroy()
        return selected_asset
    else:
        dialog.Destroy()
        return None
