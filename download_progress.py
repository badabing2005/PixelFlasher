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
#                               Class FilePickerComboBox
# ============================================================================
class DownloadProgressWindow(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Downloads Progress", style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)

        self.parent = parent
        self.SetSize((800, 500))

        self.panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.scrolled_window = wx.ScrolledWindow(self.panel)
        self.scrolled_window.SetScrollRate(0, 10)

        self.download_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scrolled_window.SetSizer(self.download_sizer)

        self.main_sizer.Add(self.scrolled_window, 1, wx.EXPAND | wx.ALL, 10)
        self.panel.SetSizer(self.main_sizer)

        # Dictionary to store download items (URL -> (gauge, cancel_button, sizer))
        self.downloads = {}

        # Center the window on parent
        self.CenterOnParent()

    def add_download(self, url, filename):
        if url in self.downloads:
            return self.downloads[url][0], self.downloads[url][1]

        item_panel = wx.Panel(self.scrolled_window)
        item_sizer = wx.BoxSizer(wx.VERTICAL)

        # URL and Filename
        label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        url_label = wx.StaticText(item_panel, label=_("Downloading: %s) % (filename))
        label_sizer.Add(url_label, 1, wx.EXPAND)

        # Progress bar and cancel button
        gauge_sizer = wx.BoxSizer(wx.HORIZONTAL)
        gauge = wx.Gauge(item_panel, range=100, size=(-1, 20), style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
        cancel_button = wx.Button(item_panel, label=_("Cancel"), size=(70, -1))

        gauge_sizer.Add(gauge, 1, wx.EXPAND | wx.RIGHT, 5)
        gauge_sizer.Add(cancel_button, 0)

        item_sizer.Add(label_sizer, 0, wx.EXPAND | wx.BOTTOM, 5)
        item_sizer.Add(gauge_sizer, 0, wx.EXPAND)

        separator = wx.StaticLine(item_panel)
        item_sizer.Add(separator, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 10)

        item_panel.SetSizer(item_sizer)
        self.download_sizer.Add(item_panel, 0, wx.EXPAND | wx.ALL, 5)

        self.downloads[url] = (gauge, cancel_button, item_panel)

        self.download_sizer.Layout()
        self.scrolled_window.FitInside()

        # Show the window if it's the first download
        if len(self.downloads) == 1:
            self.Show()

        return gauge, cancel_button

    def remove_download(self, url):
        if url in self.downloads:
            gauge, cancel_button, panel = self.downloads[url]
            panel.Destroy()
            del self.downloads[url]

            self.download_sizer.Layout()
            self.scrolled_window.FitInside()

            if not self.downloads:
                self.Hide()
