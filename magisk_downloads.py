#!/usr/bin/env python

from urllib.parse import urlparse

import darkdetect
import markdown
import wx
import wx.html
import wx.lib.mixins.listctrl as listmix
import wx.lib.wxpTag

import images as images
from runtime import *


# ============================================================================
#                               Class ListCtrl
# ============================================================================
class ListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
#                               Class MagiskDownloads
# ============================================================================
class MagiskDownloads(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        self.SetTitle("Download and Install Magisk")
        self.url =  None
        self.channel = None
        self.version = None
        self.versionCode = None
        self.filename = None
        self.release_notes = None

        vSizer = wx.BoxSizer(wx.VERTICAL)
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.Label = "Select Magisk version to install."
        self.message_label.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))

        message_sizer.Add(self.message_label, 0, wx.ALL, 20)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        vSizer.Add(message_sizer, 0, wx.EXPAND, 5)

        list_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # list control
        if self.CharHeight > 20:
            self.il = wx.ImageList(24, 24)
            self.idx1 = self.il.Add(images.Official.GetBitmap())
        else:
            self.il = wx.ImageList(16, 16)
            self.idx1 = self.il.Add(images.Official_Small.GetBitmap())
        self.list  = ListCtrl(self, -1, size=(-1, self.CharHeight * 9), style = wx.LC_REPORT)
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        device = get_phone()
        apks = device.magisk_apks

        self.list.InsertColumn(0, 'Channel', width = -1)
        self.list.InsertColumn(1, 'Version', wx.LIST_FORMAT_LEFT, -1)
        self.list.InsertColumn(2, 'VersionCode', wx.LIST_FORMAT_LEFT,  -1)
        self.list.InsertColumn(3, 'URL', wx.LIST_FORMAT_LEFT,  -1)
        self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLUE'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10).Bold())))

        i = 0
        for apk in apks:
            if apk.type != '':
                index = self.list.InsertItem(i, apk.type)
                if apk.type in ('stable', 'beta', 'canary', 'debug'):
                    self.list.SetItemColumnImage(i, 0, 0)
                else:
                    self.list.SetItemColumnImage(i, 0, -1)
            if apk.version != '':
                self.list.SetItem(index, 1, apk.version)
            if apk.versionCode != '':
                self.list.SetItem(index, 2, apk.versionCode)
            if apk.link != '':
                self.list.SetItem(index, 3, apk.link)
            i += 1

        self.list.SetColumnWidth(0, -2)
        self.list.SetColumnWidth(1, -2)
        self.list.SetColumnWidth(2, -2)
        self.list.SetColumnWidth(3, -1)

        list_sizer.Add(self.list, 1, wx.ALL|wx.EXPAND, 10)

        vSizer.Add(list_sizer , 0, wx.EXPAND, 5)

        # Release Notes
        self.html = wx.html.HtmlWindow(self, wx.ID_ANY, size=(420, -1))
        if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo:
            self.html.SetStandardFonts()
        vSizer.Add(self.html , 1, wx.EXPAND, 5)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        self.install_button = wx.Button(self, wx.ID_ANY, u"Install", wx.DefaultPosition, wx.DefaultSize, 0)
        self.install_button.SetToolTip(u"WARNING! Do not install magisk if you already have a hidden (stub) Magisk installed.\nFirst unhide Magisk before attempting an install.")
        self.install_button.Enable(False)
        buttons_sizer.Add(self.install_button, 0, wx.ALL, 20)
        self.cancel_button = wx.Button(self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 20)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        vSizer.Add(buttons_sizer, 0, wx.EXPAND, 5)

        self.SetSizer(vSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        self.install_button.Bind(wx.EVT_BUTTON, self._onOk)
        self.cancel_button.Bind(wx.EVT_BUTTON, self._onCancel)
        self.list.Bind(wx.EVT_LEFT_DOWN, self._on_apk_selected)


        # Autosize the dialog
        self.list.PostSizeEventToParent()
        self.SetSizerAndFit(vSizer)
        a = self.list.GetViewRect()
        self.SetSize(vSizer.MinSize.Width + 80, vSizer.MinSize.Height + 420)

        print("\nOpening Magisk Downloader/Installer ...")

    # -----------------------------------------------
    #                  __del__
    # -----------------------------------------------
    def __del__(self):
        pass

    # -----------------------------------------------
    #                  _onCancel
    # -----------------------------------------------
    def _onCancel(self, e):
        self.EndModal(wx.ID_CANCEL)

    # -----------------------------------------------
    #                  _on_apk_selected
    # -----------------------------------------------
    def _on_apk_selected(self, e):
        x,y = e.GetPosition()
        row,flags = self.list.HitTest((x,y))
        for i in range (0, self.list.ItemCount):
            # deselect all items
            self.list.Select(i, 0)
            item = self.list.GetItem(i)
            # reset colors
            if sys.platform == "win32":
                item.SetTextColour(wx.BLACK)
            elif darkdetect.isDark():
                item.SetTextColour(wx.WHITE)
            self.list.SetItem(item)
        if row != -1:
            self.list.Select(row)
            item = self.list.GetItem(row)
            if sys.platform == "win32":
                item.SetTextColour(wx.BLUE)
            self.list.SetItem(item)
            self.channel = self.list.GetItemText(row, col=0)
            self.version = self.list.GetItemText(row, col=1)
            self.versionCode = self.list.GetItemText(row, col=2)
            self.url = self.list.GetItemText(row, col=3)
            self.filename = os.path.basename(urlparse(self.url).path)
            device = get_phone()
            apks = device.magisk_apks
            release_notes = apks[row].release_notes
            # convert markdown to html
            self.release_notes = markdown.markdown(release_notes)
            self.html.SetPage(self.release_notes)
            self.install_button.Enable(True)
        else:
            self.install_button.Enable(False)

    # -----------------------------------------------
    #                  _onOk
    # -----------------------------------------------
    def _onOk(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
        print(f"Downloading Magisk: {self.channel} version: {self.version} versionCode: {self.versionCode} ...")
        filename = f"magisk_{self.version}_{self.versionCode}.apk"
        download_file(self.url, filename)
        config_path = get_config_path()
        app = os.path.join(config_path, 'tmp', filename)
        device = get_phone()
        device.install_apk(app, fastboot_included = True)
        # Fresh install of Magisk, reset the package name to default value
        set_magisk_package('com.topjohnwu.magisk')
        print('')
        self.EndModal(wx.ID_OK)

# ============================================================================
#                               Function download_file
# ============================================================================
def download_file(url, filename = None):
    if url:
        print (f"Downloading File: {url}")
        try:
            response = requests.get(url)
            config_path = get_config_path()
            if not filename:
                filename = os.path.basename(urlparse(url).path)
            downloaded_file_path = os.path.join(config_path, 'tmp', filename)
            open(downloaded_file_path, "wb").write(response.content)
            # check if filename got downloaded
            if not os.path.exists(downloaded_file_path):
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to download file from  {url}\n")
                print("Aborting ...\n")
                return
        except Exception:
            print (f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to download file from  {url}\n")
            return 'ERROR'
    return downloaded_file_path

