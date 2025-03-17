#!/usr/bin/env python
# coding=utf-8

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

import datetime
import wx
import wx.html
import wx.lib.wxpTag
import webbrowser
from constants import *
from runtime import get_bundle_dir
from runtime import check_latest_version
from packaging.version import parse

class AboutDlg(wx.Dialog):
    text = '''
<html>
<body bgcolor="#DCDCDC" style="font-family: Arial; background-color: #DCDCDC;">
<center>
    <img src="{0}/images/icon-dark-64.png" width="64" height="64" alt="PixelFlasher">

    <h1>PixelFlasher</h1>
    <p>By Badabing</p>
    <h3>Version {1}</h3>

    {2}

    <p>Fork the <a style="color: #004CE5;" href="https://github.com/badabing2005/PixelFlasher/fork">project on
    GitHub</a> and help improve it for all!</p>

    <p> Beware! </p>
    <p> If you are asked to donate or pay money for this program, check your source. </p>
    <p> This program is free, will always remain totally free, ad free, even donation free.</p>

    <p>
        <wxp module="wx" class="Button">
            <param name="label" value="Close">
            <param name="id" value="ID_OK">
        </wxp>
    </p>
</center>
</body>
</html>
'''

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "About PixelFlasher")
        html = HtmlWindow(self, wx.ID_ANY, size=(420, -1))
        if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo:
            html.SetStandardFonts()

        # check version if we are running the latest
        l_version = check_latest_version()
        if parse(VERSION) < parse(l_version):
            update_text = f"<p><b>Update </b> <a style=\"color: #004CE5;\" href=\"https://github.com/badabing2005/PixelFlasher/releases/latest\">Version v{l_version}</a> is available.</p>"
        else:
            update_text = "<p> You're up to date! </p>"

        txt = self.text.format(get_bundle_dir(), VERSION, update_text, datetime.datetime.now().year)
        html.SetPage(txt)
        ir = html.GetInternalRepresentation()
        html.SetSize((ir.GetWidth() + 25, ir.GetHeight() + 25))
        self.SetClientSize(html.GetSize())
        self.CentreOnParent(wx.BOTH)


class HtmlWindow(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())

