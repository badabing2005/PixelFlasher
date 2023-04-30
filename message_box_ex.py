import wx
from runtime import *

class MessageBoxEx(wx.Dialog):
    def __init__(self, *args, button_texts=None, default_button=None, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        self.SetTitle(get_message_box_title())
        self.button_texts = button_texts
        self.default_button = default_button
        self.buttons = []
        self.return_value = None

        vSizer = wx.BoxSizer(wx.VERTICAL)
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))
        self.message_label.Label = get_message_box_message()
        message_sizer.Add(self.message_label, 1, wx.ALL|wx.EXPAND, 20)
        vSizer.Add(message_sizer, 1, wx.EXPAND, 5)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        self.buttons = []
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
        self.return_value = button_index + 1
        self.EndModal(button_index + 1)

    def show(self):
        self.ShowModal()
        return self.return_value

