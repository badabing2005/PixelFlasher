#!/usr/bin/env python
# coding=utf-8

import sys
import datetime
import os
import wx
import wx.html
import wx.lib.wxpTag
import webbrowser
from config import VERSION
from modules import get_bundle_dir

class AboutDlg(wx.Dialog):
    text = '''
<html>
<body bgcolor="#DCDCDC" style="font-family: Arial; background-color: #DCDCDC;">
<center>
    <img src="{0}/images/icon-64.png" width="64" height="64" alt="PixelFlasher">

    <h1>PixelFlasher</h1>

    <p>Version {1}</p>

    <p>Fork the <a style="color: #004CE5;" href="https://github.com/badabing2005/PixelFlasher">project on
    GitHub</a> and help improve it for all!</p>

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
        txt = self.text.format(get_bundle_dir(), VERSION, datetime.datetime.now().year)
        html.SetPage(txt)
        ir = html.GetInternalRepresentation()
        html.SetSize((ir.GetWidth() + 25, ir.GetHeight() + 25))
        self.SetClientSize(html.GetSize())
        self.CentreOnParent(wx.BOTH)


class HtmlWindow(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())

