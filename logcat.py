#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from runtime import *
from i18n import _

# ============================================================================
#                               Class LogcatPanel
# ============================================================================
class LogcatPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.device = get_phone(True)
        if not self.device:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device.")
            wx.MessageBox(_("❌ ERROR: You must first select a valid device."), _("Error"), wx.OK | wx.ICON_ERROR)
            self.Close()
            return

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create UI components
        self._create_formatting_section()
        self._create_filter_section()
        self._create_buttons()

        # Set up the panel
        self.SetSizer(self.main_sizer)
        self.Layout()

    # -----------------------------------------------
    #       Function _create_formatting_section
    # -----------------------------------------------
    def _create_formatting_section(self):
        # Formatting section with a box
        formatting_box = wx.StaticBox(self, -1, _("Formatting Options"))
        formatting_sizer = wx.StaticBoxSizer(formatting_box, wx.VERTICAL)

        # Formatting checkbox
        self.format_cb = wx.CheckBox(formatting_box, -1, _("Enable formatting (-v)"))
        self.format_cb.SetToolTip(_("Enable or disable formatting options for logcat output"))
        self.format_cb.SetValue(True)  # Default is enabled
        self.format_cb.Bind(wx.EVT_CHECKBOX, self.on_format_checkbox)
        formatting_sizer.Add(self.format_cb, 0, wx.ALL, 3)

        # Container for format options
        format_options_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Format verbs - in a grid layout
        verbs_box = wx.StaticBox(formatting_box, -1, _("Format Verbs"))
        verbs_sizer = wx.StaticBoxSizer(verbs_box, wx.VERTICAL)

        verbs = [
            ("brief", _("Show priority, tag, and PID of the process issuing the message")),
            ("long", _("Show all metadata fields and separate messages with blank lines")),
            ("process", _("Show PID only")),
            ("raw", _("Show the raw log message with no other metadata fields")),
            ("tag", _("Show the priority and tag only")),
            ("thread", _("Show priority, PID, and TID of the thread issuing the message")),
            ("threadtime", _("Show date, time, priority, tag, PID, and TID (default)")),
            ("time", _("Show date, time, priority, tag, and PID of the process"))
        ]        # Create a grid of radio buttons with 2 rows, 4 columns
        verb_grid = wx.GridSizer(rows=2, cols=4, hgap=0, vgap=2)
        self.verb_radios = []

        for i, (verb, tooltip) in enumerate(verbs):
            rb = wx.RadioButton(verbs_box, -1, verb, style=wx.RB_GROUP if i == 0 else 0)
            rb.SetToolTip(tooltip)
            if verb == "long":
                rb.SetValue(True)
            self.verb_radios.append(rb)
            verb_grid.Add(rb, 0, wx.EXPAND)

        verbs_sizer.Add(verb_grid, 1, wx.ALL | wx.EXPAND, 2)

        # Adverb modifiers - in a grid layout
        adverbs_box = wx.StaticBox(formatting_box, -1, _("Adverb Modifiers"))
        adverbs_sizer = wx.StaticBoxSizer(adverbs_box, wx.VERTICAL)

        adverbs = [
            ("color", _("Show each priority with a different color")),
            ("descriptive", _("Show event descriptions from event-log-tags database")),
            ("epoch", _("Show time as seconds since 1970-01-01 (Unix epoch)")),
            ("monotonic", _("Show time as CPU seconds since boot")),
            ("printable", _("Ensure that any binary logging content is escaped")),
            ("uid", _("Show UID or Android ID of logged process (if permitted)")),
            ("usec", _("Show time with microsecond precision"))
        ]        # Create a grid of checkboxes with 2 rows, 4 columns
        adverb_grid = wx.GridSizer(rows=2, cols=4, hgap=0, vgap=2)
        self.format_adverbs_cbs = []

        for adverb, tooltip in adverbs:
            cb = wx.CheckBox(adverbs_box, -1, adverb)
            cb.SetToolTip(tooltip)
            if adverb in ["color", "descriptive"]:
                cb.SetValue(True)
            self.format_adverbs_cbs.append(cb)
            adverb_grid.Add(cb, 0, wx.EXPAND)

        adverbs_sizer.Add(adverb_grid, 1, wx.ALL | wx.EXPAND, 2)

        # Add verbs and adverbs to the format options sizer
        format_options_sizer.Add(verbs_sizer, 1, wx.RIGHT | wx.EXPAND, 2)
        format_options_sizer.Add(adverbs_sizer, 1, wx.LEFT | wx.EXPAND, 2)

        formatting_sizer.Add(format_options_sizer, 1, wx.ALL | wx.EXPAND, 2)
        self.main_sizer.Add(formatting_sizer, 0, wx.ALL | wx.EXPAND, 3)

    # -----------------------------------------------
    #              Function _create_filter_section
    # -----------------------------------------------
    def _create_filter_section(self):
        # Filter section with a box
        filter_box = wx.StaticBox(self, -1, _("Filter Options"))
        filter_sizer = wx.StaticBoxSizer(filter_box, wx.VERTICAL)

        # Container for all filter options
        filter_options_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Tag filter
        tag_box = wx.StaticBox(filter_box, -1, _("Tag Filter"))
        tag_sizer = wx.StaticBoxSizer(tag_box, wx.VERTICAL)

        tag_label = wx.StaticText(tag_box, -1, _("Tag:"))
        self.tag_input = wx.TextCtrl(tag_box, -1, "*")
        self.tag_input.SetToolTip(_("Enter log component tag (or * for all)"))

        tag_sizer.Add(tag_label, 0, wx.TOP | wx.LEFT | wx.RIGHT, 2)
        tag_sizer.Add(self.tag_input, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        # Priority filter
        priority_box = wx.StaticBox(filter_box, -1, _("Priority Level"))
        priority_sizer = wx.StaticBoxSizer(priority_box, wx.VERTICAL)

        priorities = [
            ("V", "_(Verbose (default for specific tag))"),
            ("D", "_(Debug (default for *))"),
            ("I", _("Info")),
            ("W", _("Warn")),
            ("E", _("Error")),
            ("F", _("Fatal")),
            ("S", _("Silent (suppress all output)"))
        ]        # Create a horizontal row of radio buttons
        priority_grid = wx.BoxSizer(wx.HORIZONTAL)
        self.priority_radios = []

        for i, (priority, tooltip) in enumerate(priorities):
            rb = wx.RadioButton(priority_box, -1, priority, style=wx.RB_GROUP if i == 0 else 0)
            rb.SetToolTip(tooltip)
            if priority == "D":
                rb.SetValue(True)
            self.priority_radios.append(rb)
            priority_grid.Add(rb, 0, wx.RIGHT, 1)

        priority_sizer.Add(priority_grid, 0, wx.ALL, 2)

        # Additional filters
        additional_box = wx.StaticBox(filter_box, -1, _("Additional Filters"))
        additional_sizer = wx.StaticBoxSizer(additional_box, wx.VERTICAL)        # Regex filter
        regex_label = wx.StaticText(additional_box, -1, _("Regex Filter (-e):"))
        self.regex_input = wx.TextCtrl(additional_box, -1, "")
        self.regex_input.SetToolTip(_("Enter ECMAScript regex to filter output"))

        # UID filter
        uid_label = wx.StaticText(additional_box, -1, _("UIDs Filter (comma-separated):"))
        self.uid_input = wx.TextCtrl(additional_box, -1, "")
        self.uid_input.SetToolTip(_("Enter UIDs (numeric, comma-separated)"))

        additional_sizer.Add(regex_label, 0, wx.TOP | wx.LEFT | wx.RIGHT, 2)
        additional_sizer.Add(self.regex_input, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        additional_sizer.Add(uid_label, 0, wx.TOP | wx.LEFT | wx.RIGHT, 2)
        additional_sizer.Add(self.uid_input, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        # Add all filter sections to the filter options sizer
        filter_options_sizer.Add(tag_sizer, 1, wx.RIGHT | wx.EXPAND, 2)
        filter_options_sizer.Add(priority_sizer, 1, wx.RIGHT | wx.EXPAND, 2)
        filter_options_sizer.Add(additional_sizer, 2, wx.LEFT | wx.EXPAND, 2)

        filter_sizer.Add(filter_options_sizer, 1, wx.ALL | wx.EXPAND, 2)
        self.main_sizer.Add(filter_sizer, 0, wx.ALL | wx.EXPAND, 3)

    # -----------------------------------------------
    #              Function _create_buttons
    # -----------------------------------------------
    def _create_buttons(self):
        # Buttons at the bottom
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)        # Add spacer to center the buttons
        button_sizer.Add((0, 0), 1, wx.EXPAND)

        self.view_btn = wx.Button(self, -1, _("View Logcat"))
        self.view_btn.SetToolTip(_("View logcat output with selected options"))
        self.view_btn.Bind(wx.EVT_BUTTON, self.on_view_logcat)

        self.clear_btn = wx.Button(self, -1, _("Clear Logcat"))
        self.clear_btn.SetToolTip(_("Clear logcat buffer"))
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_logcat)

        self.cancel_btn = wx.Button(self, -1, _("Cancel"))
        self.cancel_btn.SetToolTip(_("Close this panel"))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)

        button_sizer.Add(self.view_btn, 0, wx.ALL, 3)
        button_sizer.Add(self.clear_btn, 0, wx.ALL, 3)
        button_sizer.Add(self.cancel_btn, 0, wx.ALL, 3)

        # Add spacer to center the buttons
        button_sizer.Add((0, 0), 1, wx.EXPAND)

        self.main_sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 5)

    # -----------------------------------------------
    #              Function on_format_checkbox
    # -----------------------------------------------
    def on_format_checkbox(self, event):
        is_enabled = self.format_cb.GetValue()

        for radio in self.verb_radios:
            radio.Enable(is_enabled)

        for cb in self.format_adverbs_cbs:
            cb.Enable(is_enabled)

    # -----------------------------------------------
    #              Function build_logcat_args
    # -----------------------------------------------
    def build_logcat_args(self):
        args = []

        # Formatting options
        if self.format_cb.GetValue():
            format_str = ""
            # Find the selected verb
            for radio in self.verb_radios:
                if radio.GetValue():
                    format_str = radio.GetLabel()
                    break

            # Add adverb modifiers
            for cb in self.format_adverbs_cbs:
                if cb.GetValue():
                    format_str += "," + cb.GetLabel()

            if format_str:
                args.extend(["-v", format_str])

        # Filter options
        tag = self.tag_input.GetValue().strip()

        # Find the selected priority
        priority = ""
        for radio in self.priority_radios:
            if radio.GetValue():
                priority = radio.GetLabel()
                break

        # Only add the tag:priority filter if tag is not empty
        if tag:
            filter_spec = f"{tag}:{priority}"
            args.append(filter_spec)

        # Regex filter
        regex = self.regex_input.GetValue().strip()
        if regex:
            args.extend(["-e", regex])

        # UID filter
        uid = self.uid_input.GetValue().strip()
        if uid:
            args.extend(["--uid", uid])

        return args

    # -----------------------------------------------
    #              Function on_view_logcat
    # -----------------------------------------------
    def on_view_logcat(self, event):
        args = self.build_logcat_args()
        if self.device:
            self.device.logcat(args)
        else:
            wx.MessageBox(_("No device connected"), _("Error"), wx.OK | wx.ICON_ERROR)
        self.GetParent().Close()

    # -----------------------------------------------
    #              Function on_clear_logcat
    # -----------------------------------------------
    def on_clear_logcat(self, event):
        if self.device:
            self.device.logcat(["-c"])
            wx.MessageBox(_("Logcat buffer cleared"), _("Success"), wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox(_("No device connected"), _("Error"), wx.OK | wx.ICON_ERROR)

    # -----------------------------------------------
    #              Function on_cancel
    # -----------------------------------------------
    def on_cancel(self, event):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
        self.GetParent().Close()


# ============================================================================
#                               Class LogcatDialog
# ============================================================================
class LogcatDialog(wx.Dialog):
    def __init__(self, parent, title=_("Logcat")):
        wx.Dialog.__init__(self, parent, title=title, size=(580, 450))

        self.panel = LogcatPanel(self)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND | wx.ALL, 2)
        self.SetSizer(sizer)

        self.Fit()
        self.CenterOnParent()

