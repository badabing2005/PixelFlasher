import wx
import images as images
from runtime import *

# ============================================================================
#                               Class MyToolsDialog
# ============================================================================
class MyToolsDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super(MyToolsDialog, self).__init__(*args, **kw)

        self.InitUI()
        self.SetSize((600, 450))
        self.SetTitle("Customize My Tools")

    def InitUI(self):
        pnl = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        sb = wx.StaticBox(pnl, label='Add a new tool')
        sbs = wx.StaticBoxSizer(sb, orient=wx.VERTICAL)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(pnl, label='Menu Title'))
        self.title = wx.TextCtrl(pnl)
        hbox1.Add(self.title, proportion=1, flag=wx.EXPAND|wx.LEFT, border=5)
        sbs.Add(hbox1, flag=wx.ALL|wx.EXPAND, border=5)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(wx.StaticText(pnl, label='Command'))
        self.command = wx.TextCtrl(pnl)
        hbox2.Add(self.command, proportion=1, flag=wx.EXPAND|wx.LEFT, border=5)
        sbs.Add(hbox2, flag=wx.ALL|wx.EXPAND, border=5)

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3.Add(wx.StaticText(pnl, label='Arguments'))
        self.args = wx.TextCtrl(pnl)
        hbox3.Add(self.args, proportion=1, flag=wx.EXPAND|wx.LEFT, border=5)
        sbs.Add(hbox3, flag=wx.ALL|wx.EXPAND, border=5)

        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4.Add(wx.StaticText(pnl, label='Working Directory'))
        self.wd = wx.TextCtrl(pnl)
        hbox4.Add(self.wd, proportion=1, flag=wx.EXPAND|wx.LEFT, border=5)
        sbs.Add(hbox4, flag=wx.ALL|wx.EXPAND, border=5)

        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        hbox5.Add(wx.StaticText(pnl, label='Enable'))
        self.enable = wx.CheckBox(pnl)
        hbox5.Add(self.enable, flag=wx.LEFT, border=5)
        sbs.Add(hbox5, flag=wx.ALL|wx.EXPAND, border=5)

        pnl.SetSizer(sbs)
        vbox.Add(pnl, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        self.SetSizer(vbox)

        okButton = wx.Button(self, label='Ok')
        cancelButton = wx.Button(self, label='Cancel')
        hbox6 = wx.BoxSizer(wx.HORIZONTAL)
        hbox6.Add(okButton)
        hbox6.Add(cancelButton, flag=wx.LEFT, border=5)

        vbox.Add(hbox6, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        okButton.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelButton.Bind(wx.EVT_BUTTON, self.OnCancel)

    def OnOk(self, event):
        tool = {
            'title': self.title.GetValue(),
            'command': self.command.GetValue(),
            'args': self.args.GetValue(),
            'wd': self.wd.GetValue(),
            'enable': self.enable.GetValue()
        }
        self.GetParent().tools.append(tool)
        self.Destroy()

    def OnCancel(self, event):
        self.Destroy()
