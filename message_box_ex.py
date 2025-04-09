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

import darkdetect
import markdown
import wx
import wx.html

from runtime import *

class MessageBoxEx(wx.Dialog):
    def __init__(self, *args, title=None, message=None, button_texts=None, default_button=None, disable_buttons=None, is_md=False, size=(800, 600), checkbox_labels=None, checkbox_initial_values=None, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        self.SetTitle(title)
        self.button_texts = button_texts
        self.default_button = default_button
        self.buttons = []
        self.return_value = None
        self.checkboxes = []
        self.checkbox_labels = checkbox_labels
        if checkbox_initial_values is not None:
            self.checkbox_initial_values = checkbox_initial_values
        else:
            self.checkbox_initial_values = []

        vSizer = wx.BoxSizer(wx.VERTICAL)
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if is_md:
            self.html = wx.html.HtmlWindow(self, wx.ID_ANY, size=size)
            message = message.strip()  # Remove leading/trailing whitespace
            md_html = markdown.markdown(message, extensions=['extra'])

            # Adjust colors for dark mode on Mac and Linux
            if darkdetect.isDark() and sys.platform != "win32":
                dark_html = f"""
                <!DOCTYPE html>
                <html>
                <body style="background-color:#656565; color:#ffffff;">
                    {md_html}
                </body>
                </html>
                """
                self.html.SetPage(dark_html)
                if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo or sys.platform == "darwin":
                    self.html.SetStandardFonts()
            else:
                self.html.SetPage(md_html)

            self.html.Bind(wx.html.EVT_HTML_LINK_CLICKED, self._onLinkClicked)
            message_sizer.Add(self.html, 1, wx.ALL | wx.EXPAND, 20)
        else:
            self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
            self.message_label.Wrap(-1)
            self.message_label.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            self.message_label.Label = message
            message_sizer.Add(self.message_label, 1, wx.ALL | wx.EXPAND, 20)

        vSizer.Add(message_sizer, 1, wx.EXPAND, 5)

        if checkbox_labels is not None:
            checkbox_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY), wx.HORIZONTAL)
            for i in range(len(checkbox_labels)):
                checkbox_label = checkbox_labels[i]
                checkbox = wx.CheckBox(self, wx.ID_ANY, checkbox_label, wx.DefaultPosition, wx.DefaultSize, 0)
                if i < len(self.checkbox_initial_values):
                    checkbox.SetValue(self.checkbox_initial_values[i])
                self.checkboxes.append(checkbox)
                checkbox_sizer.Add(checkbox, 0, wx.ALL, 5)
            vSizer.Add(checkbox_sizer, 0, wx.EXPAND | wx.ALL, 10)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        # do this to not have any focus on the buttons, if default_button is set, then the corresponding button will have focus
        self.SetFocus()
        if button_texts is not None:
            for i, button_text in enumerate(button_texts):
                button = wx.Button(self, wx.ID_ANY, button_text, wx.DefaultPosition, wx.DefaultSize, 0)
                self.buttons.append(button)
                buttons_sizer.Add(button, 0, wx.ALL, 20)
                button.Bind(wx.EVT_BUTTON, lambda e, i=i: self._onButtonClick(e, i))
                if self.default_button == i + 1:
                    self._setDefaultButton(button)
                if disable_buttons is not None and i + 1 in disable_buttons:
                    button.Disable()
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        vSizer.Add(buttons_sizer, 0, wx.EXPAND, 5)

        self.SetSizer(vSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Autosize the dialog
        self.SetSizerAndFit(vSizer)

    def _setDefaultButton(self, button):
        button.SetDefault()
        button.SetFocus()

    def _onButtonClick(self, e, button_index):
        button_value = button_index + 1
        if self.checkbox_labels is not None:
            checkbox_values = [checkbox.IsChecked() for checkbox in self.checkboxes]
            set_dlg_checkbox_values(checkbox_values)
            self.return_value = {'button': button_value, 'checkboxes': checkbox_values}
        self.EndModal(button_value)

    def _onLinkClicked(self, event):
        url = event.GetLinkInfo().GetHref()
        # wx.LaunchDefaultBrowser(url)
        webbrowser.open(url)
