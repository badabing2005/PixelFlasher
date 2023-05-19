#!/usr/bin/env python

import webbrowser

import markdown
import wx
import wx.html

from runtime import *


class MessageBoxEx(wx.Dialog):
    def __init__(self, *args, title=None, message=None, button_texts=None, default_button=None, disable_buttons=None, is_md=False, size=(800, 600), checkbox_labels=None, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        self.SetTitle(title)
        self.button_texts = button_texts
        self.default_button = default_button
        self.buttons = []
        self.return_value = None
        self.checkboxes = []
        self.checkbox_labels = checkbox_labels

        vSizer = wx.BoxSizer(wx.VERTICAL)
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if is_md:
            self.html = wx.html.HtmlWindow(self, wx.ID_ANY, size=size)
            md_html = markdown.markdown(message)
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
            for checkbox_label in checkbox_labels:
                checkbox = wx.CheckBox(self, wx.ID_ANY, checkbox_label, wx.DefaultPosition, wx.DefaultSize, 0)
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
