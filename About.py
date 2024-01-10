#!/usr/bin/env python
# coding=utf-8

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

