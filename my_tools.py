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

import json
import json5
from datetime import datetime

import wx
import images as images
from runtime import *
from i18n import _


# ============================================================================
#                               Class MyToolsDialog
# ============================================================================
class MyToolsDialog(wx.Dialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, style=wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE)
        self.SetTitle(_("My Tools Manager"))
        self.mytools = {}
        self.load_mytools()
        self.SetSize((900, 750))

        self.list = wx.ListCtrl(parent=self, id=wx.ID_ANY, size=(-1, -1), style=wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_SINGLE_SEL)

        if sys.platform == "win32":
            self.list.SetHeaderAttr(wx.ItemAttr(colText=wx.Colour('BLACK'), colBack=wx.Colour('DARK GREY'), font=wx.Font(wx.FontInfo(10).Bold())))

        # Enable checkboxes
        if hasattr(self.list, 'EnableCheckBoxes'):
            self.list.EnableCheckBoxes()

        self.Refresh()

        self.title_ctrl = wx.SearchCtrl(self, style=wx.TE_LEFT)
        title_ctrl_default_height = self.title_ctrl.GetSize().height
        self.title_ctrl.SetMinSize((500, title_ctrl_default_height))
        self.title_ctrl.ShowCancelButton(True)
        self.title_ctrl.SetDescriptiveText(_("Title"))
        self.title_ctrl.ShowSearchButton(False)
        self.title_ctrl.SetToolTip(_("Title of the tool"))

        self.command_ctrl = wx.SearchCtrl(self, style=wx.TE_LEFT)
        self.command_ctrl.ShowCancelButton(True)
        self.command_ctrl.SetDescriptiveText(_("Command"))
        self.command_ctrl.ShowSearchButton(False)
        self.command_ctrl.SetToolTip(_("Command to run"))

        self.args_ctrl = wx.SearchCtrl(self, style=wx.TE_LEFT)
        self.args_ctrl.ShowCancelButton(True)
        self.args_ctrl.SetDescriptiveText(_("Arguments"))
        self.args_ctrl.ShowSearchButton(False)
        self.args_ctrl.SetToolTip(_("Arguments to pass to the command"))

        self.directory_ctrl = wx.SearchCtrl(self, style=wx.TE_LEFT)
        self.directory_ctrl.ShowCancelButton(True)
        self.directory_ctrl.SetDescriptiveText(_("Directory"))
        self.directory_ctrl.ShowSearchButton(False)
        self.directory_ctrl.SetToolTip(_("Directory to run the command in"))

        shell_method_choices = [_("Method 1"), _("Method 2"), _("Method 3"), _("Method 4")]
        self.shell_method_choice = wx.Choice(self, choices=shell_method_choices)
        self.shell_method_choice.SetSelection(2)
        self.shell_method_choice.SetToolTip(_("Shell method to use\nMethod 3 is recommended."))

        self.run_detached_checkbox = wx.CheckBox(self, label=_("Run Detached"))
        self.run_detached_checkbox.SetValue(True)
        self.run_detached_checkbox.SetToolTip(_("Run the command detached"))

        self.enabled_checkbox = wx.CheckBox(self, label=_("Enabled"))
        self.enabled_checkbox.SetToolTip(_("Enable the tool"))

        self.add_button = wx.Button(self, label=_("Add"))
        self.add_button.SetToolTip(_("Add a new tool"))
        self.add_button.Disable()

        self.add_separator = wx.Button(self, label=_("Add Separator"))
        self.add_separator.SetToolTip(_("Add a separator"))
        self.add_separator.Disable()

        self.remove_button = wx.Button(self, label=_("Remove"))
        self.remove_button.SetToolTip(_("Remove the selected tool"))
        self.remove_button.Disable()

        self.update_button = wx.Button(self, label=_("Update"))
        self.update_button.SetToolTip(_("Update the selected tool"))
        self.update_button.Disable()

        self.up_button = wx.Button(self, label=_("Up"))
        self.up_button.SetToolTip(_("Move selected tool up"))
        self.up_button.Disable()

        self.down_button = wx.Button(self, label=_("Down"))
        self.down_button.SetToolTip(_("Move selected tool down"))
        self.down_button.Disable()

        self.close_button = wx.Button(self, label=_("Close"))
        self.close_button.SetToolTip(_("Close this dialog"))

        vSizer = wx.BoxSizer(wx.VERTICAL)

        entry_vSizer = wx.BoxSizer(wx.VERTICAL)
        entry_vSizer.Add(self.title_ctrl, 0, wx.ALL|wx.EXPAND, 10)
        entry_vSizer.Add(self.command_ctrl, 0, wx.ALL|wx.EXPAND, 10)
        entry_vSizer.Add(self.args_ctrl, 0, wx.ALL|wx.EXPAND, 10)
        entry_vSizer.Add(self.directory_ctrl, 0, wx.ALL|wx.EXPAND, 10)
        entry_vSizer.Add(self.shell_method_choice, 0, wx.ALL|wx.EXPAND, 10)
        entry_vSizer.Add(self.run_detached_checkbox, 0, wx.ALL|wx.EXPAND, 10)
        entry_vSizer.Add(self.enabled_checkbox, 0, wx.ALL|wx.EXPAND, 10)
        entry_vSizer.AddSpacer(40)
        entry_vSizer.Add(self.add_button, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        entry_vSizer.Add(self.add_separator, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        entry_vSizer.Add(self.remove_button, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        entry_vSizer.Add(self.update_button, 0, wx.EXPAND | wx.ALL, 10)
        entry_vSizer.Add(self.up_button, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        entry_vSizer.Add(self.down_button, 0, wx.EXPAND | wx.ALL, 10)
        entry_vSizer.AddStretchSpacer()
        entry_vSizer.Add(self.close_button, 0, wx.EXPAND | wx.ALL, 10)

        main_hSizer = wx.BoxSizer(wx.HORIZONTAL)
        main_hSizer.Add(self.list, 1, wx.ALL|wx.EXPAND, 10)
        main_hSizer.Add(entry_vSizer, 2, wx.ALL|wx.EXPAND, 0)

        vSizer.Add(main_hSizer , 1, wx.ALL|wx.EXPAND, 10)

        self.SetSizer(vSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        self.list.PostSizeEventToParent()
        self.SetSizerAndFit(vSizer)

        # Connect Events
        self.add_button.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.add_separator.Bind(wx.EVT_BUTTON, self.OnAddSeparator)
        self.remove_button.Bind(wx.EVT_BUTTON, self.OnRemove)
        self.update_button.Bind(wx.EVT_BUTTON, self.OnUpdate)
        self.up_button.Bind(wx.EVT_BUTTON, self.OnMoveUp)
        self.down_button.Bind(wx.EVT_BUTTON, self.OnMoveDown)
        self.close_button.Bind(wx.EVT_BUTTON, self.OnClose)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeSelected, self.list)
        self.title_ctrl.Bind(wx.EVT_TEXT, self.on_command_change)
        self.args_ctrl.Bind(wx.EVT_TEXT, self.on_args_change)
        self.directory_ctrl.Bind(wx.EVT_TEXT, self.on_directory_change)
        self.Bind(wx.EVT_SIZE, self.OnResize)

    # -----------------------------------------------
    #              Function PopulateList
    # -----------------------------------------------
    def PopulateList(self):
        try:
            self.list.ClearAll()  # Clear existing items and columns
            self.list.InsertColumn(0, "Tools", width=wx.LIST_AUTOSIZE_USEHEADER)

            min_width = 250  # Minimum column width
            max_width = 500  # Maximum column width
            max_text_width = 0  # Track the maximum text width

            if self.mytools:
                for key, data in self.mytools.items():
                    index = self.list.InsertItem(self.list.GetItemCount(), data["title"])
                    if data["enabled"]:
                        self.list.CheckItem(index, check=True)
                    else:
                        self.list.SetItemTextColour(index, wx.Colour(128, 128, 128))
                        self.list.CheckItem(index, check=False)

                    # Measure text width of the current item
                    text_width = self.list.GetTextExtent(data["title"])[0]
                    if text_width > max_text_width:
                        max_text_width = text_width

            # Adjust column width based on text width, within min and max bounds
            column_width = max(min_width, min(max_text_width + 30, max_width))
            self.list.SetColumnWidth(0, column_width)

            self.list.GetParent().Layout()
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()

    # -----------------------------------------------
    #                  on_command_change
    # -----------------------------------------------
    def on_command_change(self, event):
        text = self.title_ctrl.GetValue()
        if text.strip():
            self.add_button.Enable()
            self.add_separator.Enable()
            self.remove_button.Enable()
        else:
            self.add_button.Disable()
            self.add_separator.Disable()
            self.remove_button.Disable()

    # -----------------------------------------------
    #                  on_args_change
    # -----------------------------------------------
    def on_args_change(self, event):
        self.update_button.Enable()

    # -----------------------------------------------
    #                  on_directory_change
    # -----------------------------------------------
    def on_directory_change(self, event):
        self.update_button.Enable()

    # -----------------------------------------------
    #                  load_mytools
    # -----------------------------------------------
    def load_mytools(self):
        if os.path.exists(get_mytools_file_path()):
            try:
                with open(get_mytools_file_path(), "r", encoding='ISO-8859-1', errors="replace") as file:
                    data = json5.load(file)
                    self.mytools = data.get('tools', {})
                    self.count = data.get('count', 0)
            except FileNotFoundError:
                self.mytools = {}
                self.count = 0
        else:
            self.mytools = {}
            self.count = 0

    # -----------------------------------------------
    #                  save_mytools
    # -----------------------------------------------
    def save_mytools(self):
        data = {
            'tools': self.mytools,
            'count': self.count
        }
        with open(get_mytools_file_path(), "w", encoding='ISO-8859-1', errors="replace") as file:
            json.dump(data, file, indent=4)

    # -----------------------------------------------
    #                  OnClose
    # -----------------------------------------------
    def OnClose(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Close Customize My Tools Dialog")
        self.EndModal(wx.ID_CANCEL)

    # -----------------------------------------------
    #                  OnAdd
    # -----------------------------------------------
    def OnAdd(self, e):
        try:
            if self.title_ctrl.Value:
                self._on_spin('start')
                self.add_to_mytools()
                self._on_spin('stop')
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while adding to mytools")
            puml("#red:Encountered an error while adding to mytools;\n")
            self._on_spin('stop')
            traceback.print_exc()

    # -----------------------------------------------
    #                  OnAddSeparator
    # -----------------------------------------------
    def OnAddSeparator(self, e):
        try:
            if self.title_ctrl.Value:
                self._on_spin('start')
                self.add_to_mytools(separator=True)
                self._on_spin('stop')
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while adding to mytools")
            puml("#red:Encountered an error while adding to mytools;\n")
            self._on_spin('stop')
            traceback.print_exc()

    # -----------------------------------------------
    #                  OnRemove
    # -----------------------------------------------
    def OnRemove(self, e):
        selection = self.list.GetFirstSelected()
        if selection != -1:
            item_id = str(selection + 1)
            self.list.DeleteItem(selection)
            if item_id in self.mytools:
                del self.mytools[item_id]
                # Renumber the remaining items
                new_mytools = {}
                for new_index, (old_key, value) in enumerate(self.mytools.items(), start=1):
                    new_mytools[str(new_index)] = value
                self.mytools = new_mytools
                # Update count
                self.count = len(self.mytools)
                self.save_mytools()
                self.Refresh()

    # -----------------------------------------------
    #                  OnUpdate
    # -----------------------------------------------
    def OnUpdate(self, e):
        selection = self.list.GetFirstSelected()
        if selection == -1:
            print(f"No item selected for update.")
            return
        item_id = str(selection + 1)
        self.add_to_mytools(update_index=item_id)
        self.list.Select(selection)

    # -----------------------------------------------
    #                  OnMoveUp
    # -----------------------------------------------
    def OnMoveUp(self, e):
        selection = self.list.GetFirstSelected()
        # Check if it's not the first item
        if selection > 0:
            # Swap items in self.mytools
            item_id = str(selection + 1)
            above_item_id = str(selection)
            self.mytools[item_id], self.mytools[above_item_id] = self.mytools[above_item_id], self.mytools[item_id]

            # Update GUI list
            self.RefreshList()
            # Select the item in its new position
            self.list.Select(selection - 1)

    # -----------------------------------------------
    #                  OnMoveDown
    # -----------------------------------------------
    def OnMoveDown(self, e):
        selection = self.list.GetFirstSelected()
        # Check if it's not the last item
        if selection < self.list.GetItemCount() - 1:
            # Swap items in self.mytools
            item_id = str(selection + 1)
            below_item_id = str(selection + 2)
            self.mytools[item_id], self.mytools[below_item_id] = self.mytools[below_item_id], self.mytools[item_id]

            self.RefreshList()
            # Select the item in its new position
            self.list.Select(selection + 1)

    # -----------------------------------------------
    #                  OnItemDeSelected
    # -----------------------------------------------
    def OnItemDeSelected(self, event):
        self.title_ctrl.Clear()
        self.command_ctrl.Clear()
        self.args_ctrl.Clear()
        self.directory_ctrl.Clear()
        self.enabled_checkbox.SetValue(False)
        self.up_button.Disable()
        self.down_button.Disable()
        self.remove_button.Disable()
        self.update_button.Disable()
        event.Skip()

    # -----------------------------------------------
    #                  OnItemSelected
    # -----------------------------------------------
    def OnItemSelected(self, event):
        item_index = event.Index
        item_id = str(item_index + 1)

        if item_id in self.mytools:
            tool_data = self.mytools[item_id]

            # Update UI controls with the selected tool's data
            self.title_ctrl.SetValue(tool_data.get("title", ""))
            self.command_ctrl.SetValue(tool_data.get("command", ""))
            self.args_ctrl.SetValue(tool_data.get("arguments", ""))
            self.directory_ctrl.SetValue(tool_data.get("directory", ""))
            self.enabled_checkbox.SetValue(tool_data.get("enabled", False))
            self.shell_method_choice.SetStringSelection(tool_data.get("method", "Method 3"))
            self.shell_method_choice.Enable()
            self.run_detached_checkbox.SetValue(tool_data.get("detached", True))
            self.run_detached_checkbox.Enable()
            self.update_button.Enable()
            self.remove_button.Enable()

            if item_index == 0:
                self.up_button.Disable()
            else:
                self.up_button.Enable()

            if item_index == len(self.mytools) - 1:
                self.down_button.Disable()
            else:
                self.down_button.Enable()
        else:
            print(f"Tool ID {item_id} not found in the tools list.")

        event.Skip()

    # -----------------------------------------------
    #          Function add_to_mytools
    # -----------------------------------------------
    def add_to_mytools(self, update_index=None, separator=False):
        if separator:
            title = "---"
            command = ""
            arguments = ""
            directory = ""
            enabled = True
            method = "Method 3"
            detached = False
        else:
            title = self.title_ctrl.GetValue()
            command = self.command_ctrl.GetValue()
            arguments = self.args_ctrl.GetValue()
            directory = self.directory_ctrl.GetValue()
            enabled = self.enabled_checkbox.GetValue()
            method = self.shell_method_choice.GetStringSelection()
            detached = self.run_detached_checkbox.GetValue()
        record = {
            "title": title,
            "command": command,
            "arguments": arguments,
            "directory": directory,
            "method": method,
            "detached": detached,
            "enabled": enabled
        }
        if update_index is None:
            # Adding a new tool
            self.count += 1
            self.mytools[str(self.count)] = record
        else:
            # Updating an existing tool
            if str(update_index) in self.mytools:
                self.mytools[str(update_index)] = record
            else:
                print(f"No tool found at index {update_index} to update.")
        self.save_mytools()
        self.Refresh()

    # -----------------------------------------------
    #                  Function Refresh
    # -----------------------------------------------
    def Refresh(self):
        self.list.Freeze()
        self.list.ClearAll()
        self.PopulateList()
        self.list.Thaw()

    # -----------------------------------------------
    #                  Function RefreshList
    # -----------------------------------------------
    def RefreshList(self):
        self.list.DeleteAllItems()
        sorted_tools = sorted(self.mytools.items(), key=lambda x: int(x[0]))
        for item_id, tool in sorted_tools:
            # Insert each tool's title into the list at the next available index
            index = self.list.InsertItem(self.list.GetItemCount(), tool['title'])
        self.save_mytools()

    # -----------------------------------------------
    #                  Function OnResize
    # -----------------------------------------------
    def OnResize(self, event):
        list_size = self.list.GetSize()
        self.list.SetColumnWidth(0, list_size.GetWidth() - 5)
        self.Layout()
        # event.Skip()

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
