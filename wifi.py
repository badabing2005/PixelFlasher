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

import contextlib
import json
import json5
from datetime import datetime

import wx
import wx.html
import wx.lib.mixins.listctrl as listmix
import wx.lib.wxpTag

import images as images
from phone import get_connected_devices
from runtime import *

dark_green = wx.Colour(0, 100, 0)

# ============================================================================
#                               Class ListCtrl
# ============================================================================
class ListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


# ============================================================================
#                               Class Wireless
# ============================================================================
class Wireless(wx.Dialog, listmix.ColumnSorterMixin):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs, style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE)
        self.SetTitle("ADB Wireless")
        self.history = {}
        self.load_history()

        self.searchCtrl = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.searchCtrl.ShowCancelButton(True)

        self.il = wx.ImageList(16, 16)
        # self.idx1 = self.il.Add(images.official_16.GetBitmap())
        self.sm_up = self.il.Add(images.SmallUpArrow.GetBitmap())
        self.sm_dn = self.il.Add(images.SmallDnArrow.GetBitmap())

        self.list = ListCtrl(self, -1, size=(-1, -1), style=wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_SINGLE_SEL)

        if sys.platform == "win32":
            self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLACK'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10).Bold())))
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.list.EnableCheckBoxes(enable=False)
        listmix.ColumnSorterMixin.__init__(self, 6)
        self.Refresh()

        self.ip_ctrl = wx.SearchCtrl(self, style=wx.TE_LEFT)
        ip_ctrl_default_height = self.ip_ctrl.GetSize().GetHeight()
        self.ip_ctrl.SetMinSize((200, ip_ctrl_default_height))
        self.ip_ctrl.ShowCancelButton(True)
        self.ip_ctrl.SetDescriptiveText("IP/Hostname")
        self.ip_ctrl.ShowSearchButton(False)

        self.port = wx.SearchCtrl(self, style=wx.TE_LEFT)
        self.port.ShowCancelButton(True)
        self.port.SetDescriptiveText("Port (Default:5555)")
        self.port.ShowSearchButton(False)

        self.pairing_code = wx.SearchCtrl(self, style=wx.TE_LEFT)
        self.pairing_code.ShowCancelButton(True)
        self.pairing_code.SetDescriptiveText("Pairing Code")
        self.pairing_code.ShowSearchButton(False)

        self.connect_button = wx.Button(self, wx.ID_ANY, u"Connect", wx.DefaultPosition, wx.DefaultSize, 0)
        self.connect_button.SetToolTip(u"Connect to device")
        self.connect_button.Disable()

        self.disconnect_button = wx.Button(self, wx.ID_ANY, u"Disconnect", wx.DefaultPosition, wx.DefaultSize, 0)
        self.disconnect_button.SetToolTip(u"Disconnect device")
        self.disconnect_button.Disable()

        self.pair_button = wx.Button(self, wx.ID_ANY, u"Pair", wx.DefaultPosition, wx.DefaultSize, 0)
        self.pair_button.SetToolTip(u"Pairs with device (only needed once per device)")
        self.pair_button.Disable()

        self.close_button = wx.Button(self, wx.ID_ANY, u"Close", wx.DefaultPosition, wx.DefaultSize, 0)
        self.close_button.SetToolTip(u"Closes this dialog")

        vSizer = wx.BoxSizer(wx.VERTICAL)
        search_hsizer = wx.BoxSizer( wx.HORIZONTAL )
        search_hsizer.Add(self.searchCtrl, 1, wx.ALL, 20)

        entry_vSizer = wx.BoxSizer(wx.VERTICAL)
        entry_vSizer.Add(self.ip_ctrl, 0, wx.ALL|wx.EXPAND, 10)
        entry_vSizer.Add(self.port, 0, wx.ALL|wx.EXPAND, 10)
        entry_vSizer.Add(self.pairing_code, 0, wx.ALL|wx.EXPAND, 10)
        entry_vSizer.AddSpacer(40)
        entry_vSizer.Add(self.connect_button, 0, wx.EXPAND | wx.ALL, 10)
        entry_vSizer.Add(self.disconnect_button, 0, wx.EXPAND | wx.ALL, 10)
        entry_vSizer.Add(self.pair_button, 0, wx.EXPAND | wx.ALL, 10)
        entry_vSizer.Add((0, 0), proportion=1, flag=wx.EXPAND, border=0)
        entry_vSizer.Add(self.close_button, 0, wx.EXPAND | wx.ALL, 10)

        main_hSizer = wx.BoxSizer(wx.HORIZONTAL)
        main_hSizer.Add(self.list, 1, wx.ALL|wx.EXPAND, 10)
        main_hSizer.Add(entry_vSizer, 0, wx.ALL|wx.EXPAND, 0)

        vSizer.Add(search_hsizer, 0, wx.EXPAND, 10)
        vSizer.Add(main_hSizer , 1, wx.ALL|wx.EXPAND, 10)

        self.SetSizer(vSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Autosize the dialog
        self.list.PostSizeEventToParent()
        self.SetSizerAndFit(vSizer)
        self.SetSize(vSizer.MinSize.Width + 80, vSizer.MinSize.Height + 400)

        # Connect Events
        self.searchCtrl.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.searchCtrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.searchCtrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.connect_button.Bind(wx.EVT_BUTTON, self.OnConnect)
        self.disconnect_button.Bind(wx.EVT_BUTTON, self.OnDisconnect)
        self.pair_button.Bind(wx.EVT_BUTTON, self.OnPair)
        self.close_button.Bind(wx.EVT_BUTTON, self.OnClose)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeSelected, self.list)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
        self.ip_ctrl.Bind(wx.EVT_TEXT, self.on_ip_change)
        self.pairing_code.Bind(wx.EVT_TEXT, self.on_pairing_change)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    # -----------------------------------------------
    #              Function PopulateList
    # -----------------------------------------------
    def PopulateList(self):
        try:
            info = wx.ListItem()
            info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
            info.Image = -1
            info.Align = 0
            info.Width = -1
            info.SetWidth(-1)
            info.Text = "Date"
            self.list.InsertColumn(0, info)

            info.Align = wx.LIST_FORMAT_LEFT # 0
            info.Text = "Action"
            self.list.InsertColumn(1, info)

            info.Align = wx.LIST_FORMAT_LEFT # 0
            info.Text = "IP/Hostname"
            self.list.InsertColumn(2, info)

            info.Align = wx.LIST_FORMAT_LEFT # 0
            info.Text = "Port"
            self.list.InsertColumn(3, info)

            info.Align = wx.LIST_FORMAT_LEFT # 0
            info.Text = "Pairing Code"
            self.list.InsertColumn(4, info)

            info.Align = wx.LIST_FORMAT_LEFT # 0
            info.Text = "Note"
            self.list.InsertColumn(5, info)

            itemDataMap = {}
            query = self.searchCtrl.GetValue().lower()
            if self.history:
                i = 0
                items = self.history.items()
                # date in epoch is the key
                for key, data in items:
                    action = data["action"]
                    ip = data["ip"]
                    port = data["port"]
                    pair = data["pair"]
                    if pair is None:
                        pair = ''
                    note = data["note"]
                    if note is None:
                        note = ''
                    status = data["status"]
                    ts = datetime.fromtimestamp(int(key))
                    action_date = ts.strftime('%Y-%m-%d %H:%M:%S')
                    alltext = f"{action_date} {action.lower()} {status.lower()} {ip.lower()} {port.lower()} {pair.lower()} {note.lower()}"
                    if query.lower() in alltext:
                        index = self.list.InsertItem(self.list.GetItemCount(), action_date)
                        itemDataMap[i + 1] = (key, action, ip, port, pair, note)
                        row = self.list.GetItem(index)
                        self.list.SetItem(index, 1, action)
                        self.list.SetItem(index, 2, ip)
                        self.list.SetItem(index, 3, port)
                        self.list.SetItem(index, 4, pair)
                        self.list.SetItem(index, 5, note)
                        if status == 'Success':
                            row.SetTextColour(dark_green)
                        elif status == 'Failed':
                            row.SetTextColour(wx.RED)
                        self.list.SetItem(row)
                        self.list.SetItemData(index, i + 1)
                        # hide image
                        self.list.SetItemColumnImage(i, 0, -1)
                        i += 1
            self.list.SetColumnWidth(0, -2)
            grow_column(self.list, 0, 20)
            self.list.SetColumnWidth(1, -2)
            grow_column(self.list, 1, 20)
            self.list.SetColumnWidth(2, -2)
            grow_column(self.list, 1, 40)
            self.list.SetColumnWidth(3, -2)
            grow_column(self.list, 1, 40)
            self.list.SetColumnWidth(4, -2)
            grow_column(self.list, 1, 20)
            self.list.SetColumnWidth(5, 200)
            grow_column(self.list, 1, 20)

            self.currentItem = 0
            if itemDataMap:
                return itemDataMap
            else:
                return -1
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while populating wifi history")
            puml("#red:Encountered an error while populating wifi history;\n")
            traceback.print_exc()

    # -----------------------------------------------
    #                  on_ip_change
    # -----------------------------------------------
    def on_ip_change(self, event):
        text = self.ip_ctrl.GetValue()
        if text.strip():
            self.connect_button.Enable()
            self.disconnect_button.Enable()
        else:
            self.connect_button.Disable()
            self.disconnect_button.Disable()

    # -----------------------------------------------
    #                  on_pairing_change
    # -----------------------------------------------
    def on_pairing_change(self, event):
        text = self.pairing_code.GetValue()
        if text.strip():
            self.pair_button.Enable()
        else:
            self.pair_button.Disable()

    # -----------------------------------------------
    #                  onSearch
    # -----------------------------------------------
    def OnSearch(self, event):
        query = self.searchCtrl.GetValue()
        print(f"Searching for: {query}")
        self.Refresh()

    # -----------------------------------------------
    #                  onCancel
    # -----------------------------------------------
    def OnCancel(self, event):
        self.searchCtrl.SetValue("")
        self.Refresh()

    # -----------------------------------------------
    #                  load_history
    # -----------------------------------------------
    def load_history(self):
        if os.path.exists(get_wifi_history_file_path()):
            with contextlib.suppress(FileNotFoundError):
                with open(get_wifi_history_file_path(), "r", encoding='ISO-8859-1', errors="replace") as file:
                    self.history = json5.load(file)

    # -----------------------------------------------
    #                  save_history
    # -----------------------------------------------
    def save_history(self):
        with open(get_wifi_history_file_path(), "w", encoding='ISO-8859-1', errors="replace") as file:
            json.dump(self.history, file, indent=4)

    # -----------------------------------------------
    #                  OnClose
    # -----------------------------------------------
    def OnClose(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Close.")
        self.EndModal(wx.ID_CANCEL)

    # ============================================================================
    #                               Function wifi_adb_action
    # ============================================================================
    def wifi_adb_action(self, ip, port = "5555", disconnect = False, pairing_code = ''):
        if disconnect:
            command = 'disconnect'
        elif pairing_code != '':
            command = 'pair'
        else:
            command = 'connect'
        print(f"Remote ADB {command}ing: {ip}:{port} {pairing_code}")
        if get_adb():
            puml(":Wifi ADB;\n", True)
            ip = ip.strip()
            port = port.strip()
            if port == '':
                port = "5555"
            theCmd = f"\"{get_adb()}\" {command} {ip}:{port} {pairing_code}"
            res = run_shell(theCmd)
            puml(f"note right\n=== {command} to: {ip}:{port} {pairing_code}\nend note\n")
            if res.returncode == 0 and 'cannot' not in res.stdout and 'failed' not in res.stdout:
                print(f"ADB {command}ed: {ip}:{port}")
                puml(f"#palegreen:Succeeded;\n")
                if command != 'pair':
                    self.Parent.device_choice.SetItems(get_connected_devices())
                    self.Parent._select_configured_device()
                    print(f"Please select the device: {ip}:{port}")
                return
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not {command} {ip}:{port} {pairing_code}\n")
                print(f"{res.stderr}")
                print(f"{res.stdout}")
                puml(f"#red:**Failed**\n{res.stderr}\n{res.stdout};\n")
                return f"{res.stderr} {res.stdout}"

    # -----------------------------------------------
    #                  OnConnect
    # -----------------------------------------------
    def OnConnect(self, e):
        try:
            if self.ip_ctrl.Value:
                self._on_spin('start')
                res = self.wifi_adb_action(self.ip_ctrl.Value, self.port.Value)
                if res:
                    self.add_to_history(action='connect', status="Failed", note=res)
                else:
                    self.add_to_history(action='connect', status="Success")
                    port = self.port.Value
                    if port == '':
                        port = "5555"
                    device_id = f"{self.ip_ctrl.Value}:{port}"
                    set_phone_id(device_id)
                    self.Parent.config.device = device_id
                    self.Parent.refresh_device(device_id)
                self._on_spin('stop')
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while wifi connecting")
            puml("#red:Encountered an error while wifi connecting;\n")
            self._on_spin('stop')
            traceback.print_exc()

    # -----------------------------------------------
    #                  OnDisconnect
    # -----------------------------------------------
    def OnDisconnect(self, e):
        try:
            if self.ip_ctrl.Value:
                self._on_spin('start')
                res = self.wifi_adb_action(self.ip_ctrl.Value, self.port.Value, disconnect=True)
                if res:
                    self.add_to_history(action='disconnect', status="Failed", note=res)
                else:
                    self.add_to_history(action='disconnect', status="Success")
                    self.Parent.device_choice.Popup()
                self._on_spin('stop')
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while disconnecting a wireless device")
            puml("#red:Encountered an error while disconnecting a wireless device;\n")
            self._on_spin('stop')
            traceback.print_exc()

    # -----------------------------------------------
    #                  OnPair
    # -----------------------------------------------
    def OnPair(self, e):
        try:
            if self.pairing_code.Value:
                self._on_spin('start')
                res = self.wifi_adb_action(self.ip_ctrl.Value, self.port.Value, disconnect=False, pairing_code=self.pairing_code.Value)
                if res is None:
                    self.add_to_history(action='pair', status="Success")
                else:
                    self.add_to_history(action='pair', status="Failed", note=res)
                self._on_spin('stop')
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while pairing a device")
            puml("#red:Encountered an error while pairing a device;\n")
            self._on_spin('stop')
            traceback.print_exc()

    # -----------------------------------------------
    #                  GetListCtrl
    # -----------------------------------------------
    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.list

    # -----------------------------------------------
    #                  GetSortImages
    # -----------------------------------------------
    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)


    # -----------------------------------------------
    #                  getColumnText
    # -----------------------------------------------
    def getColumnText(self, index, col):
        item = self.list.GetItem(index, col)
        return item.GetText()

    # -----------------------------------------------
    #                  OnItemSelected
    # -----------------------------------------------
    def OnItemDeSelected(self, event):
        self.ip_ctrl.Clear()
        self.port.Clear()
        self.pairing_code.Clear()
        event.Skip()

    # -----------------------------------------------
    #                  OnItemSelected
    # -----------------------------------------------
    def OnItemSelected(self, event):
        self.currentItem = event.Index
        self.ip_ctrl.SetValue(self.getColumnText(self.currentItem, 2))
        self.port.SetValue(self.getColumnText(self.currentItem, 3))
        if self.getColumnText(self.currentItem, 4).strip() != '':
            self.pairing_code.SetValue(self.getColumnText(self.currentItem, 4))
        event.Skip()

    # -----------------------------------------------
    #                  OnColClick
    # -----------------------------------------------
    def OnColClick(self, event):
        col = event.GetColumn()
        if col == -1:
            return # clicked outside any column.
        rowid = self.list.GetColumn(col)
        # print(f"Sorting on Column {rowid.GetText()}")
        event.Skip()

    # -----------------------------------------------
    #          Function simulate_column_click
    # -----------------------------------------------
    def simulate_column_click(self, col):
        fake_event = wx.ListEvent(wx.EVT_LIST_COL_CLICK.typeId, self.list.GetId())
        fake_event.SetEventObject(self.list)
        fake_event.SetColumn(col)
        self.list.ProcessEvent(fake_event)

    # -----------------------------------------------
    #          Function add_to_history
    # -----------------------------------------------
    def add_to_history(self, action, status, note=None):
        ip = self.ip_ctrl.GetValue()
        port = self.port.GetValue()
        pair = self.pairing_code.GetValue()
        record = {
            "action": action,
            "status": status,
            "ip": ip,
            "port": port,
            "pair": pair,
            "note": note
        }
        current_timestamp = int(time.time())
        self.history[str(current_timestamp)] = record
        self.save_history()
        self.Refresh()

    # -----------------------------------------------
    #                  Function Refresh
    # -----------------------------------------------
    def Refresh(self):
        self.list.Freeze()
        self.list.ClearAll()
        itemDataMap = self.PopulateList()
        if itemDataMap != -1:
            self.itemDataMap = itemDataMap
        # reverse sort by date
        self.simulate_column_click(0)
        self.simulate_column_click(0)
        self.list.Thaw()

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
